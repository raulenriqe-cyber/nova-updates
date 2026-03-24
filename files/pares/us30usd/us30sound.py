#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔊 US30 GILGAMESH SOUND ENGINE - Edge-TTS Neural Voices                    ║
║  by Polarice Labs © 2026                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Premium Female Voice: JennyNeural (Ultra-Natural)                           ║
║  250+ Wall Street & Gilgamesh Phrases | Emotion-based Speech Rate            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, json, struct, threading, time, random, asyncio, tempfile, os, subprocess
from pathlib import Path
from datetime import datetime

# ============ CONFIGURATION ============
PORT = 8970  # ⭐ MUST match quantum_core.py
LOG_FILE = Path(__file__).parent / "logs" / "sound_engine.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# 🔗 Communication validation timeouts for Swiss precision
COMMUNICATION_TIMEOUT = 3.0  # Maximum time to wait for response
MESSAGE_VALIDATION_ENABLED = True  # Validate incoming messages
AUDIO_QUALITY_THRESHOLD = 0.7  # Minimum confidence for audio alerts

# Simple file logging
def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except (UnicodeEncodeError, UnicodeDecodeError):
        print(line.encode('ascii', 'replace').decode('ascii'))
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

# ============ EDGE-TTS ============
try:
    import edge_tts
    TTS_AVAILABLE = True
    log("✓ edge-tts available")
except ImportError:
    TTS_AVAILABLE = False
    log("⚠ edge-tts not installed - pip install edge-tts")

# Voice
VOICE = 'en-US-JennyNeural'

# Emotion rates
EMOTION_RATES = {
    'PANIC': '+5%',
    'EXCITED': '+5%',
    'NORMAL': '-5%',
    'CALM': '-10%',
    'SAD': '-15%'
}

# 250+ WALL STREET & GILGAMESH PHRASES - US30 Dow Jones Edition
# Gilgamesh: King of Uruk, 2/3 god, conqueror of Humbaba, slayer of the Bull of Heaven
# Wall Street: NYSE floor, blue chips, Dow Jones 30, institutional power
PHRASES = {
    'BUY': [
        "GILGAMESH RISES! The King of Uruk storms Wall Street - the Dow bows before us!",
        "The Bull of Heaven charges through the NYSE floor - BUY with divine fury!",
        "Wall Street opens the gates - Gilgamesh leads the thirty blue chips to WAR!",
        "The opening bell ROARS - like Enkidu in the wilderness, we attack with primal force!",
        "Dow Jones ascending - Gilgamesh climbs the Cedar Mountain of PROFIT!",
        "The trading floor ERUPTS - institutional bulls stampede through resistance!",
        "Like Gilgamesh facing Humbaba - we fear NOTHING in this market!",
        "Blue chip rally INITIATED - the walls of Uruk stand unbreakable!",
        "NYSE specialists scramble - Gilgamesh has entered the arena!",
        "The Dow surges upward - like Gilgamesh lifting the gates of Uruk!",
        "BULL RUN CONFIRMED - Wall Street trembles before our buying power!",
        "Gilgamesh and Enkidu united - two-thirds divine, ALL profit!",
        "The thirty giants of the Dow AWAKEN - blue chips march to war!",
        "Morgan Stanley weeps - Gilgamesh takes their lunch money!",
        "Corporate earnings CRUSHED expectations - the index flies like Shamash's chariot!",
        "Wall Street's fear index drops - Gilgamesh brings ORDER to chaos!",
        "The Federal Reserve bows - even gods respect momentum THIS strong!",
        "Institutional money flows IN - like the great flood in reverse!",
        "Hedge funds scramble to cover - Gilgamesh SQUEEZES the shorts!",
        "The Dow punches through resistance - like Gilgamesh through the Cedar Forest!",
        "Goldman Sachs upgrades - even the priests of Wall Street see our power!",
        "Market makers retreat - Gilgamesh claims the bid-ask spread as tribute!",
        "The floor traders CHEER - blue chip momentum is UNSTOPPABLE!",
        "Like the walls of Uruk - our position is FORTIFIED and rising!",
        "VIX crushed to dust - Gilgamesh tramples fear beneath his sandals!",
        "The Dow breaks all-time highs - Gilgamesh writes history in GREEN candles!",
        "IPO frenzy unleashed - Wall Street celebrates like Uruk's festivals!",
        "The bond market capitulates - equities are Gilgamesh's KINGDOM!",
        "S&P futures confirm - the Dow rides higher on Gilgamesh's chariot!",
        "Dark pools flooding BUY orders - institutional Enkidu leads the charge!",
        "Earnings season EXPLODES upward - Gilgamesh feasts on profits!",
        "The Cedar Forest conquered - every resistance level FALLS before us!",
        "Market breadth expanding - ALL thirty components march north!",
        "Gilgamesh forges the path - from Uruk to the New York Stock Exchange!",
        "The trading algorithms BOW - no machine can match Gilgamesh's vision!",
        "Pension funds deploy capital - the smart money follows Gilgamesh!",
        "Tech sector leads the charge - Gilgamesh rides the NASDAQ winds too!",
        "The Dow industrials ROAR - thirty blue chips in perfect formation!",
        "Like Utnapishtim surviving the flood - we survive and THRIVE in this rally!",
        "Wall Street's finest salute - Gilgamesh has spoken, the market OBEYS!",
        "The opening auction EXPLODES - bulls charging like the sacred bull of Ishtar!",
        "Federal stimulus CONFIRMED - Gilgamesh surfs the liquidity wave!",
        "Block trades flowing upward - institutional Gilgamesh claims his throne!",
        "The Dow's golden cross appears - Gilgamesh sees the path to IMMORTALITY!",
        "Short sellers CRUSHED - Gilgamesh breaks their chains like Enkidu's cage!",
        "Sector rotation BULLISH - every industry bows to the King of Uruk!",
        "The closing bell approaches - Gilgamesh secures the day's CONQUEST!",
        "Commodities confirm - even crude oil fuels Gilgamesh's war machine!",
        "The thirty titans RISE - Dow Jones components in perfect HARMONY!",
        "Gilgamesh decree: The market shall RISE and all bears shall KNEEL!"
    ],
    'SELL': [
        "GILGAMESH DESCENDS! The King attacks from ABOVE - ride the red candles DOWN!",
        "Wall Street CRUMBLES - Gilgamesh commands the bears to feast!",
        "The Dow plunges - like Enkidu's descent to the underworld, we profit from the fall!",
        "SHORT THE INDEX - Gilgamesh sees the weakness in the blue chips!",
        "Humbaba's curse on the market - the Cedar Forest BURNS and we ride the smoke DOWN!",
        "Circuit breakers ACTIVATED - Gilgamesh pushes through every floor!",
        "The NYSE floor in PANIC - traders flee, but Gilgamesh attacks the downside!",
        "Dow futures collapse - Gilgamesh foresaw this when the stars of Anu dimmed!",
        "Ishtar's REVENGE on the market - the Bull of Heaven is SLAIN, the Dow falls!",
        "Institutional selling CONFIRMED - Gilgamesh leads the exodus from the top!",
        "The Fed raised rates - Gilgamesh saw the storm before the gods themselves!",
        "Hedge funds DUMP positions - Gilgamesh rides the avalanche to profit!",
        "VIX EXPLODES upward - fear index rises as Gilgamesh conquers the downside!",
        "Market makers pulling bids - like the gods withdrawing favor from Uruk!",
        "Goldman downgrades EVERYTHING - even the priests abandon the temple!",
        "The yield curve INVERTS - Gilgamesh reads the omen of recession!",
        "Dark pools flooding SELL orders - institutional bears follow our king!",
        "Earnings miss CATASTROPHIC - blue chips crumble like the walls of lesser cities!",
        "The death cross forms - Gilgamesh recognizes mortality in the chart!",
        "Flash crash IMMINENT - Gilgamesh surfs the waterfall of red candles!",
        "Bond yields SPIKE - the smart money flees equities for safety!",
        "Short interest EXPLODING - Gilgamesh leads the short brigade!",
        "The Dow breaks critical support - like Enkidu breaking the door of the Cedar Forest!",
        "Margin calls EVERYWHERE - leverage unwinds as Gilgamesh predicted!",
        "CPI data CRUSHES bulls - inflation is the serpent that stole the plant of youth!",
        "Pentagon of resistance holds - every bounce is a chance to SHORT harder!",
        "The thirty blue chips in FREEFALL - not even Boeing can keep them airborne!",
        "Market breadth COLLAPSES - fewer stocks holding, the index must follow DOWN!",
        "Gilgamesh sees the void below - the underworld has PROFITS waiting!",
        "The tape reads pure distribution - smart money exits, we SHORT alongside!",
        "Treasury yields scream DANGER - like the scorpion men guarding the mountain!",
        "The Dow's moving averages CROSS - death follows, and Gilgamesh profits!",
        "Retail capitulation begins - weak hands feed OUR short position!",
        "Geopolitical chaos erupts - Gilgamesh THRIVES in the fog of war!",
        "Options put volume SURGES - the market bets WITH Gilgamesh's vision!",
        "The closing auction DRAGS lower - sellers dominant as Uruk's armies!",
        "Liquidity DRIES UP - like the desert of Mashu, only Gilgamesh survives!",
        "S&P correlation DRAGS the Dow - all indices bow to gravity!",
        "The afterhours sell-off CONFIRMS - Gilgamesh's bearish thesis was DIVINE!",
        "Fund managers panic-sell into the close - Gilgamesh remains CALM and SHORT!",
        "Fibonacci retracement FAILS - the abyss below has no support!",
        "The Dow gaps DOWN at open - Gilgamesh feasts on overnight terror!",
        "Sector rotation INTO bonds - the great migration from equities begins!",
        "Market sentiment CRASHES - like Gilgamesh mourning Enkidu, but WE profit!",
        "Block trades all hitting the BID - institutional Gilgamesh presses DOWN!",
        "The nonfarm payrolls DISAPPOINT - the economy bows before reality!",
        "Commodity crash DRAGS industrials - the Dow's heavy weights sink FAST!",
        "Volatility expansion CONFIRMED - Gilgamesh surfs the chaos to the underworld!",
        "The serpent of inflation steals growth - Gilgamesh rides the serpent DOWN!",
        "SHORT CONFIRMED - Gilgamesh attacks the red candles with divine precision!"
    ],
    'TP': [
        "THE WALLS OF URUK SHINE! Gilgamesh counts his SPOILS - take profit SECURED!",
        "Wall Street just paid TRIBUTE to the King of Uruk - profits LOCKED IN!",
        "The Dow delivered our price - like the gods granting Gilgamesh's wish!",
        "TAKE PROFIT HIT! Gilgamesh's strategy was FLAWLESS - the market OBEYED!",
        "The thirty blue chips delivered GOLD - Gilgamesh builds another wing on Uruk's walls!",
        "Target price SMASHED - like Gilgamesh smashing Humbaba's defenses!",
        "TP ACHIEVED! The Cedar Forest's treasures are OURS!",
        "Profits extracted with surgical precision - Gilgamesh, the MASTER TRADER!",
        "The NYSE just crowned us KING - take profit like Wall Street royalty!",
        "Gilgamesh returns to Uruk VICTORIOUS - the city celebrates our GAINS!",
        "Position closed in GLORY - the Dow danced to Gilgamesh's rhythm!",
        "PROFITS SECURED! Even Shamash the Sun God approves this trade!",
        "The Bull of Heaven's horns are our TROPHY - take profit COMPLETE!",
        "Wall Street whispers our name - Gilgamesh, the PROFIT KING!",
        "The trade unfolds PERFECTLY - like the epic carved on tablets of lapis lazuli!",
        "Institutional money DELIVERED - Gilgamesh rides the flow to VICTORY!",
        "TP smashed through like Enkidu through the temple gates - TRIUMPHANT!",
        "The Dow gave us EXACTLY what we demanded - divine profits SECURED!",
        "Risk-reward ratio PERFECTED - Gilgamesh's mathematics are LEGENDARY!",
        "Closing bell rings in our FAVOR - another day, another CONQUEST!",
        "The smart money AGREES - Gilgamesh called it RIGHT, profits extracted!",
        "Blue chip gains BANKED - like storing treasures in Uruk's royal vaults!",
        "FLAWLESS EXECUTION - the trading floor applauds Gilgamesh's precision!",
        "Hedge fund returns PALE next to ours - take profit CHAMPION TIER!",
        "The algorithm executed PERFECTLY - Gilgamesh's code is DIVINE!",
        "Profit factor EXCELLENT - every point captured like a Cedar Forest tree!",
        "The Dow's price action obeyed our levels - Gilgamesh COMMANDS the market!",
        "Target reached AHEAD of schedule - time is Gilgamesh's servant!",
        "VICTORY COMPLETE! Even the scorpion men of Mashu bow before our gains!",
        "The trade was carved in stone - like the Epic itself, ETERNAL profit!",
        "Take profit TRIGGERED - the market paid its debt to the King!",
        "Position squared at MAXIMUM profit - Gilgamesh never leaves gains on the table!",
        "The thirty titans DELIVERED - Dow components aligned FOR our profit!",
        "Portfolio mark-to-market: LEGENDARY - Gilgamesh builds wealth like Uruk's walls!",
        "TP levels BREACHED upward - even better than projected, DIVINE accuracy!",
        "The trading day BELONGS to Gilgamesh - profits flow like the Euphrates!",
        "Sharpe ratio THIS trade: INFINITE - risk managed, reward CAPTURED!",
        "The closing auction CONFIRMS our genius - Gilgamesh's timing was PERFECT!",
        "Profits EXTRACTED from the Dow like cedar wood from the forest - PREMIUM!",
        "Another chapter in the Epic of PROFIT - Gilgamesh's legend GROWS!",
        "Take profit ORDER FILLED - the serpent cannot steal THIS treasure!",
        "Wall Street FUNDED our ambition - Gilgamesh reinvests into POWER!",
        "The trade completed its JOURNEY - from entry to TP, pure GILGAMESH!",
        "Points HARVESTED from the index - the King of Uruk farms the Dow!",
        "Absolute DOMINATION - the market obeyed every fibonacci to the tick!",
        "The profit CHALICE overflows - like the tavern keeper Siduri's wine!",
        "MISSION ACCOMPLISHED - Gilgamesh's US30 campaign was PERFECTION!",
        "The Dow paid us in FULL - every point, every tick, all OURS!",
        "Epic VICTORY - the tablets of profit are inscribed in Uruk's walls!",
        "TAKE PROFIT SUPREME - Gilgamesh walks among mortals AND profits!"
    ],
    'SL': [
        "Gilgamesh mourns like losing Enkidu - but the King of Uruk RISES AGAIN!",
        "The market struck like Humbaba's roar - wounds heal, traders ADAPT!",
        "Stop loss triggered - even Gilgamesh lost the plant of immortality, yet he endured!",
        "Wall Street took our toll - but Uruk's walls still STAND!",
        "The Dow bit back - like the serpent stealing the sacred herb, we learn!",
        "Ishtar's curse struck our position - but Gilgamesh defied GODS and survived!",
        "Flash crash caught us - but the Cedar Forest has MORE trees to conquer!",
        "Stop hit - the scorpion men wounded us, but we CROSS the mountain again!",
        "Market volatility CONSUMED us - like the flood consumed the world, yet Utnapishtim survived!",
        "The position fell - but Gilgamesh built Uruk's walls AFTER his greatest losses!",
        "Risk management SAVED us - the stop was the shield of the King!",
        "Blue chip betrayal - even the mightiest stocks stumble, Gilgamesh KNOWS this!",
        "The Dow reversed HARD - like Enkidu's fate was sealed, so was this trade!",
        "Stop triggered at support - the underworld took this one, but NOT us!",
        "Institutional traps CAUGHT us - but Gilgamesh escaped Humbaba's LARGER traps!",
        "The serpent wins THIS round - but Gilgamesh has INFINITE patience!",
        "VIX spike destroyed our entry - but the King rebuilds STRONGER!",
        "The Fed's words crushed us - like the gods flooding the earth, but we SURVIVED!",
        "Position stopped - every loss is a TABLET in Gilgamesh's wisdom!",
        "The market gods tested us - Gilgamesh passed EVERY test before!",
        "The trade died in the Cedar Forest - but the WOOD of wisdom remains!",
        "Drawdown absorbed - like Uruk absorbs attacks, the walls HOLD!",
        "The Dow gap destroyed us - but gaps FILL and Gilgamesh RETURNS!",
        "Loss taken with DIGNITY - even two-thirds god feels pain, then CONQUERS!",
        "The stop was our SHIELD - without it, the loss would be the flood itself!",
        "Earnings surprise CRUSHED the position - but next earnings, Gilgamesh STRIKES!",
        "The black candle swallowed us - but Gilgamesh has seen DARKER nights!",
        "Market manipulation caught our stop - but the King plays a LONGER game!",
        "The thirty blue chips turned against us - like the gods turning on mankind!",
        "Slippage widened the loss - but Gilgamesh's capital is his ARMY, still strong!",
        "The trade journals this loss - like scribes recording Gilgamesh's battles!",
        "Index whipsaw caught both sides - but the King only needs ONE good trade!",
        "The stop saved our KINGDOM - losing a battle to WIN the war!",
        "Overnight gap destroyed the setup - but dawn brings NEW opportunities!",
        "Correlation breakdown hurt us - but Gilgamesh adapts to ANY market!",
        "The nonfarm payrolls were our Humbaba - fierce, but survivable!",
        "Platform latency cost us - but the next strike will be FASTER!",
        "The position bled slowly - death by a thousand ticks, but we CUT it clean!",
        "Sector rotation crushed our thesis - but Gilgamesh ROTATES with the market!",
        "The algo hunters found our stop - but the King sets BETTER traps next time!",
        "Weekly close below support - a painful ending, but Monday brings REBIRTH!",
        "The drawdown was significant - but Gilgamesh's capital survives to fight!",
        "Bond auction SHOCKED the market - external forces, but we ENDURE!",
        "The Cedar Forest burned OUR position - but from ashes, the King REBUILDS!",
        "That loss will make the NEXT trade sharper - Gilgamesh learns from EVERYTHING!",
        "The market taught us HUMILITY - even kings kneel before the tape!",
        "Stop loss was WISDOM not weakness - Gilgamesh's greatest strength is SURVIVAL!",
        "The Dow laughed at our entry - but Gilgamesh has the LAST laugh, always!",
        "Position liquidated - but liquidation is not DEATH, it's a NEW beginning!",
        "Like Gilgamesh returning to Uruk empty-handed - but WISER, always WISER!"
    ],
    'HOLD': [
        "Gilgamesh surveys the market from Uruk's walls - patience is the weapon of KINGS.",
        "The Dow is consolidating - even the King of Uruk waits for the perfect moment.",
        "No signal on Wall Street - Gilgamesh sharpens his sword while the market sleeps.",
        "Sideways action on the thirty - the Cedar Forest is quiet before the STORM.",
        "Holding position - like Gilgamesh before the gates of the Cedar Forest, PREPARING.",
        "The market whispers nothing - even Shamash sends no omens today.",
        "NYSE volume dries up - Gilgamesh reads the tablets and WAITS.",
        "No trade worthy of the King - Gilgamesh does not waste arrows on sparrows.",
        "The Dow chops sideways - the serpent sleeps, but Gilgamesh watches every breath.",
        "Patience mode ACTIVATED - Uruk was built over YEARS, not minutes.",
        "Wall Street lunch hour - even the gods rest between battles.",
        "Market indecision reigns - Gilgamesh knows indecision precedes EXPLOSIVE moves.",
        "The tape reads NEUTRAL - like the calm waters of the Euphrates before the flood.",
        "Holding with divine patience - Gilgamesh waited MILLENNIA for immortality.",
        "The blue chips hover - thirty titans in perfect BALANCE, waiting for a catalyst.",
        "No setup meets our standards - Gilgamesh attacks only WORTHY opponents.",
        "VIX compressed to nothing - the spring coils tighter, Gilgamesh FEELS it.",
        "S&P futures flat - even the broader market respects the SILENCE.",
        "The algorithms are hunting stops - Gilgamesh sees through their TRICKS.",
        "Pre-market reveals nothing - the Sun God Shamash has not yet risen.",
        "The chart builds a base - like Uruk's foundations, SOLID before the tower rises.",
        "Options expiration approaching - Gilgamesh waits for the pin to RESOLVE.",
        "No institutional footprint detected - without the whales, Gilgamesh holds POSITION.",
        "The Dow's daily range shrinks - compression before EXPANSION, patience pays.",
        "Lunch hour liquidity gone - trading now would dishonor the King's precision.",
        "Risk-off sentiment everywhere - Gilgamesh does not fight the RIVER's current.",
        "The economic calendar is EMPTY - no catalysts, no trades, only wisdom.",
        "Bollinger bands SQUEEZE - Gilgamesh recognizes the pattern, the breakout COMES.",
        "The thirty components DISAGREE - when generals fight, the King waits for CLARITY.",
        "After-hours irrelevant - Gilgamesh trades only in the COLOSSEUM of regular hours.",
        "Sector rotation unclear - the winds change, Gilgamesh reads them FIRST.",
        "The chart needs MORE data - like a scribe needing more clay, we WAIT.",
        "No confirmation from the tape - Gilgamesh requires PROOF before action.",
        "Market makers widening spreads - the battlefield is being SET, not fought.",
        "The RSI lingers at fifty - perfect NEUTRALITY, the calm before Gilgamesh STRIKES.",
        "Earnings blackout period - the blue chips are SILENT, so are we.",
        "The Dow tests a level for the THIRD time - Gilgamesh counts the touches.",
        "No momentum in either direction - even Enkidu rested between BATTLES.",
        "The weekly candle forms an INSIDE bar - the market COILS, we wait.",
        "Treasury auction approaching - Gilgamesh waits for the gods to SPEAK.",
        "Volume profile shows BALANCE - the market is FAIR, no edge to exploit yet.",
        "Asia session for US30 means NOTHING - Gilgamesh trades the New York ARENA.",
        "The chart whispers patience - and Gilgamesh ALWAYS listens before striking.",
        "Mid-week consolidation - the Dow RESTS, Gilgamesh prepares for FRIDAY's battle.",
        "No divergences detected - every indicator agrees on NOTHING, so we WAIT.",
        "The smart money is ABSENT - without Enkidu, Gilgamesh waits for his companion.",
        "Pre-FOMC silence - the market holds its BREATH, and so does the King.",
        "The Dow's VWAP is flat - no institutional direction, NO trade for Gilgamesh.",
        "Like the calm between Gilgamesh's epic battles - this SILENCE breeds the next LEGEND.",
        "The King of Uruk watches and WAITS - for the perfect US30 setup will COME."
    ]
}

# ============ TTS PLAYER ============
def play_mp3_mci(path):
    """Play MP3 using Windows MCI - Most reliable method"""
    try:
        import ctypes
        winmm = ctypes.windll.winmm
        
        # Open and play
        alias = f"mp3_{int(time.time()*1000)}"
        
        # MCI commands
        cmd_open = f'open "{path}" type mpegvideo alias {alias}'
        cmd_play = f'play {alias} wait'
        cmd_close = f'close {alias}'
        
        # Execute MCI string command
        mci_send = winmm.mciSendStringW
        buf = ctypes.create_unicode_buffer(256)
        
        result = mci_send(cmd_open, buf, 256, 0)
        if result != 0:
            log(f"MCI open error: {result}")
            return False
            
        result = mci_send(cmd_play, buf, 256, 0)
        mci_send(cmd_close, buf, 256, 0)
        
        return True
    except Exception as e:
        log(f"MCI error: {e}")
        return False

def play_mp3_wmp(path):
    """Play MP3 using Windows Media Player COM object - NO WINDOW"""
    try:
        # Use Windows Media Player via PowerShell (hidden, no window)
        ps_script = f'''
Add-Type -AssemblyName presentationCore
$mediaPlayer = New-Object System.Windows.Media.MediaPlayer
$mediaPlayer.Open([System.Uri]"{path}")
$mediaPlayer.Volume = 1.0
Start-Sleep -Milliseconds 300
$mediaPlayer.Play()
while ($mediaPlayer.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 100 }}
$duration = $mediaPlayer.NaturalDuration.TimeSpan.TotalSeconds
Start-Sleep -Seconds ($duration + 0.3)
$mediaPlayer.Close()
'''
        # Run PowerShell hidden
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        
        proc = subprocess.Popen(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.wait(timeout=30)
        return True
    except Exception as e:
        log(f"WMP error: {e}")
        return False

def play_mp3_simple(path):
    """Simple fallback - use start command"""
    try:
        # Hide the window using start /min
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        
        subprocess.Popen(
            f'start /min "" "{path}"',
            shell=True,
            startupinfo=startupinfo
        )
        # Estimate duration
        time.sleep(max(3, len(open(path, 'rb').read()) / 8000))
        return True
    except Exception as e:
        log(f"Simple play error: {e}")
        return False

def speak_tts(text, rate='+0%'):
    """Play text with edge-tts neural voice"""
    if not TTS_AVAILABLE:
        return False
    
    try:
        communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate)
        
        # Create temp file in current directory for easier access
        tmp_dir = Path(__file__).parent / "temp_audio"
        tmp_dir.mkdir(exist_ok=True)
        tmp_path = str(tmp_dir / f"speech_{int(time.time()*1000)}.mp3")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(communicate.save(tmp_path))
        finally:
            loop.close()
        
        log(f"🎵 Audio saved: {tmp_path}")
        
        # Try MCI first (most reliable), then WMP, then simple fallback
        if not play_mp3_mci(tmp_path):
            log("MCI failed, trying WMP...")
            if not play_mp3_wmp(tmp_path):
                log("WMP failed, trying simple...")
                play_mp3_simple(tmp_path)
        
        # Cleanup after delay
        def cleanup():
            time.sleep(5)
            try:
                os.remove(tmp_path)
            except:
                pass
        threading.Thread(target=cleanup, daemon=True).start()
        
        return True
        
    except Exception as e:
        log(f"TTS error: {e}")
        return False

def play_beep(action):
    """Fallback beep"""
    try:
        import winsound
        if action == 'BUY':
            winsound.Beep(1000, 300)
            winsound.Beep(1200, 300)
        elif action == 'SELL':
            winsound.Beep(600, 300)
            winsound.Beep(400, 300)
        elif action == 'TP':
            winsound.Beep(1500, 200)
            winsound.Beep(1500, 200)
        elif action == 'SL':
            winsound.Beep(300, 500)
        else:
            winsound.Beep(800, 200)
    except:
        pass

# ============ PLAY ALERT ============
def play_alert(action, symbol='US30'):
    """Play audio alert"""
    action = action.upper()
    if action not in PHRASES:
        action = 'HOLD'
    
    phrase = random.choice(PHRASES[action])
    
    emotion_map = {
        'BUY': 'EXCITED',
        'SELL': 'PANIC',
        'TP': 'EXCITED',
        'SL': 'SAD',
        'HOLD': 'CALM'
    }
    emotion = emotion_map.get(action, 'NORMAL')
    rate = EMOTION_RATES.get(emotion, '+0%')
    
    log(f"🔊 {action} | {emotion} | '{phrase[:40]}...'")
    
    def audio_thread():
        if TTS_AVAILABLE:
            if not speak_tts(phrase, rate):
                play_beep(action)
        else:
            play_beep(action)
    
    t = threading.Thread(target=audio_thread, daemon=True)
    t.start()

# ============ CLIENT HANDLER ============
def handle_client(sock, addr):
    try:
        header = sock.recv(4)
        if not header or len(header) < 4:
            return
        
        # ⭐ Little-endian to match quantum_core.py
        msg_len = struct.unpack('<I', header)[0]
        if msg_len > 10000:
            return
        
        msg = b''
        while len(msg) < msg_len:
            chunk = sock.recv(min(1024, msg_len - len(msg)))
            if not chunk:
                break
            msg += chunk
        
        data = json.loads(msg.decode('utf-8'))
        action = data.get('action', 'HOLD').upper()
        symbol = data.get('symbol', 'US30').upper()
        
        play_alert(action, symbol)
        
        response = json.dumps({'status': 'ok'}).encode('utf-8')
        sock.sendall(struct.pack('<I', len(response)) + response)
        
    except Exception as e:
        log(f"Client error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

# ============ MAIN ============
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('127.0.0.1', PORT))
        server.listen(5)
        
        print("\n" + "═"*60)
        print("  🔊 US30 GILGAMESH SOUND ENGINE - Edge-TTS Neural Voices")
        print("═"*60)
        print(f"  ✓ Listening on 127.0.0.1:{PORT}")
        print(f"  ✓ TTS Engine: {'edge-tts (Neural)' if TTS_AVAILABLE else 'winsound (Beeps)'}")
        print(f"  ✓ Voice: {VOICE}")
        print("═"*60)
        print("\n  [READY] Waiting for alerts from quantum_core.py...\n")
        
        log(f"Sound Engine started on port {PORT}")
        
        while True:
            try:
                server.settimeout(0.5)
                client, addr = server.accept()
                t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print("\n  [SHUTDOWN] Sound Engine stopping...")
                break
            
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"\n  [ERROR] Port {PORT} already in use!")
            print(f"  [FIX] netstat -ano | findstr {PORT}")
            print(f"  [FIX] taskkill /F /PID <PID>")
        else:
            print(f"\n  [ERROR] {e}")
    finally:
        server.close()

if __name__ == '__main__':
    main()