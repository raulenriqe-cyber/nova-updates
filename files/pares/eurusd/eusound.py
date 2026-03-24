#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔊 NOVA SOUND ENGINE - Edge-TTS Neural Voices                               ║
║  EURUSD M15 - Sniper Predator Edition                                        ║
║  by Polarice Labs © 2026                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Premium Female Voice: JennyNeural (Ultra-Natural)                           ║
║  200+ Sarcastic Trading Phrases | Emotion-based Speech Rate                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import sys, os
# ⭐ EURUSD: Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 LOAD PORTS FROM CENTRALIZED CONFIG (euconfig.yaml)
# ═══════════════════════════════════════════════════════════════════════════
try:
    from eu_config_loader import get_sound_port
    EU_CONFIG_LOADED = True
except ImportError:
    EU_CONFIG_LOADED = False

import socket, json, struct, threading, time, random, asyncio, tempfile, subprocess
from pathlib import Path
from datetime import datetime

# ============ CONFIGURATION EURUSD M15 ============
# 🔧 FIXED: Was 6560 - MUST match euquantum_core.py Config.SOUND_PORT
if EU_CONFIG_LOADED:
    try:
        PORT = get_sound_port()
    except:
        PORT = 6570  # Fallback
else:
    PORT = 6570  # Default EURUSD sound port
LOG_FILE = Path(__file__).parent / "logs" / "sound_engine.log"
LOG_FILE.parent.mkdir(exist_ok=True)

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

# 200+ Ultra-Funny, High-Level Sarcastic Phrases (English Edition - Maximum Hype)
PHRASES = {
    'BUY': [
        "BUY BUY BUY! We're going full degenerate ape mode – to the moon or to therapy!",
        "YOLO activated! Throwing more money at this than my ex threw at therapy.",
        "Moon mission launched – if this crashes, at least we'll have a cool story.",
        "FOMO hitting harder than my morning coffee – we're in!",
        "This chart is basically screaming 'BUY ME' in Comic Sans.",
        "All in, no regrets, just vibes and impending financial ruin.",
        "My therapist said 'diversify' – I heard 'buy more of this shit'.",
        "This is the trade that will finally make my mom proud... or disown me.",
        "Buying because the stars aligned... and also because I'm bored.",
        "If this goes up, I'm a genius. If it tanks, it's 'market manipulation'.",
        "Diamond hands loading... wallet crying... ego inflating.",
        "This coin is basically my new girlfriend – volatile but exciting.",
        "Buying the dip like it's Black Friday at the apocalypse.",
        "My portfolio said 'stop', but my gut said 'send it, king'.",
        "This is not gambling, this is 'strategic capital allocation'.",
        "We buying so hard the SEC is gonna send us a fruit basket.",
        "Green candles incoming or I'm deleting my trading app forever.",
        "This trade is riskier than texting your ex at 3 AM.",
        "Buying because the chart looks like my ex's mood swings – unpredictable but hot.",
        "To the moon, Alice! Or at least to the next support level.",
        "If this pumps, drinks on me. If it dumps, therapy on me.",
        "My DD is basically 'trust me bro' with extra steps.",
        "Buying so aggressively even the bots are jealous.",
        "This is the way... straight to either Valhalla or ramen noodles.",
        "My risk management is crying, but my greed is clapping.",
        "We're not buying, we're 'accumulating at discount'.",
        "This chart is hotter than my ex's new boyfriend – must have.",
        "FOMO is real and it's wearing my face right now.",
        "Buying because logic is overrated and vibes are forever.",
        "This trade will either make me rich or make me learn Spanish.",
        "All my money is in crypto now – living the dream, dying inside.",
        "If this fails, blame the Illuminati. If it wins, credit me.",
        "Buying like it's the last day of the bull market.",
        "My portfolio is basically a cry for help at this point.",
        "This is fine. Everything is fine. We're buying anyway.",
        "Moon or bust – and bust means ramen for a month.",
        "We're not addicted, we're 'passionately invested'.",
        "This coin is my soulmate – toxic, volatile, and expensive.",
        "Buying the dip so hard the whales are taking notes.",
        "My blood type is FOMO positive – we're in deep.",
        "This trade is basically financial Russian roulette with extra steps.",
        "If we win, I'm buying a yacht. If we lose, I'm buying ramen.",
        "The market is wrong, we're right – classic trader energy.",
        "Buying because my horoscope said 'take risks today'.",
        "This is not impulse buying, this is 'strategic aggression'.",
        "We're going long so hard gravity is getting jealous.",
        "My wallet is screaming, but my ego is louder.",
        "This is the trade that will finally pay for my therapy.",
        "Buying because 'why not' is my life motto.",
        "If this pumps, I'm quitting my job. If it dumps, I'm quitting life.",
        "Diamond hands, paper heart – we're in this together."
    ],
    'SELL': [
        "SELL EVERYTHING! The ship is sinking faster than my dating life!",
        "Paper hands activated – we're bailing like it's 2008 all over again.",
        "Exit stage left before the SEC shows up with handcuffs.",
        "Selling faster than I ghost my matches on Tinder.",
        "This trade went from 'genius' to 'divorce papers' real quick.",
        "Cut losses like a pro – or like a scared child, same thing.",
        "My portfolio is bleeding redder than my ex's lipstick.",
        "Selling because the chart said 'get out while you still can'.",
        "Taking the L gracefully... or at least while screaming internally.",
        "This is called 'strategic capitulation' – sounds better than panic.",
        "Selling before my therapist has to increase my dosage.",
        "Goodbye, sweet gains – hello, ramen budget.",
        "The market just kicked me in the nuts – time to run.",
        "Selling because dignity is expensive and I'm broke.",
        "This coin betrayed me harder than my last relationship.",
        "Exit plan executed – now where's the whiskey?",
        "Selling so fast even the bots can't keep up.",
        "My stop loss finally did something right – thanks, buddy.",
        "This trade is over – time to pretend it never happened.",
        "Selling because 'hold forever' is for suckers and bagholders.",
        "The chart turned redder than my face when I check my balance.",
        "Taking profits? Nah, taking losses like a gentleman.",
        "Selling because FOMO turned into FO GO (fear of going broke).",
        "This is not selling, this is 'portfolio rebalancing'.",
        "My hands are shaking, but my sell button is steady.",
        "Selling before the IRS asks for their cut.",
        "This trade went from moonshot to dirt nap real quick.",
        "Goodbye, position – hello, self-respect (maybe).",
        "Selling because hope is not a strategy... apparently.",
        "The market said 'nope' – so I'm saying 'bye'.",
        "Taking the L and pretending it's character development.",
        "Selling faster than I delete embarrassing tweets.",
        "This is why I have a day job.",
        "My portfolio is now on life support – pulling the plug.",
        "Selling because my therapist needs a new car.",
        "This trade is dead – long live the next bad idea.",
        "Exit achieved – dignity... not so much.",
        "Selling before the crash turns my portfolio into a meme.",
        "The dip was too deep – I'm drowning.",
        "Selling because 'buy the dip' was a lie.",
        "This is called 'learning' – expensive learning.",
        "Goodbye, crypto – hello, savings account.",
        "Selling like my life depends on it... because it kinda does.",
        "The chart lied to me – time for revenge selling.",
        "Paper hands? More like diamond panic.",
        "Selling because the universe clearly hates me.",
        "This trade is over – cue the sad violin.",
        "Taking the loss and blaming the Fed.",
        "Selling before my mom finds out.",
        "The market won this round – but I'm coming back stronger.",
        "Exit complete – now where's the ice cream?"
    ],
    'TP': [
        "TAKE PROFIT BABY! We just printed money like the Fed on steroids!",
        "We did it! Profits secured – time to flex on the bears.",
        "Bag secured, haters crushed – living the dream!",
        "Take profit hit! I'm officially too rich to check prices.",
        "We won! Champagne for everyone... except the sellers.",
        "Profits locked in – my therapist can take a vacation.",
        "Target smashed! Now I can finally buy that thing I didn't need.",
        "Green candles everywhere – the market loves me today!",
        "We just turned pixels into real money – genius level unlocked.",
        "Take profit executed – now I'm a whale... kinda.",
        "This trade was perfect – I'm basically Warren Buffett 2.0.",
        "Profits so fat my wallet is on a diet.",
        "We hit TP! My mom can finally stop asking for money.",
        "Winning feels better than revenge sex.",
        "Take profit – because I'm not greedy... okay, maybe a little.",
        "The market paid me – I'm officially a professional gambler.",
        "Profits locked! Now I can afford therapy for my losses.",
        "We did the thing! Gold star for me.",
        "TP hit – my portfolio is smiling for the first time.",
        "This is what winning looks like – pure, unfiltered glory.",
        "Take profit! Now I can buy that yacht... in Monopoly.",
        "We crushed it! Bears are crying in their mom's basement.",
        "Profits secured – time to update my LinkedIn to 'investor'.",
        "This trade was flawless – I'm a god among men.",
        "TP achieved! My ego is now too big for my head.",
        "We just banked a fat W – victory dance incoming.",
        "Profits so good I might even pay taxes... nah.",
        "Take profit hit! The haters are seething.",
        "This is the best feeling since... well, ever.",
        "We won the trade – now where's my medal?",
        "Profits locked in – living rent-free in the bears' heads.",
        "TP smashed! My portfolio is throwing a party.",
        "We did it! Now I can afford to lose again.",
        "Take profit – because I'm responsible... sometimes.",
        "This trade paid off – I'm basically a financial wizard.",
        "Profits secured! Time to flex on Discord.",
        "We hit the target – my confidence is at all-time high.",
        "Take profit! The market just bought me dinner.",
        "Winning streak activated – don't stop me now!",
        "TP hit – my ex is gonna regret leaving me.",
        "We just printed money – I'm rich... on paper.",
        "Profits locked! Now I can finally sleep.",
        "This is what success tastes like – expensive and sweet.",
        "Take profit executed – haters gonna hate, winners gonna win.",
        "We did the impossible – now let's do it again.",
        "Profits so good I might even tip my barber extra.",
        "TP smashed! My portfolio is now Instagram-worthy.",
        "We won! Time to update my bio to 'successful trader'.",
        "Take profit – because I'm not greedy... much.",
        "This trade was perfect – I'm a legend.",
        "Profits secured! The bears can cry in the corner."
    ],
    'SL': [
        "Stop loss hit... ouch. My wallet just filed for divorce.",
        "SL activated – capital preserved, dignity... not so much.",
        "We took the L – but at least it was a stylish L.",
        "Stop loss saved me from total annihilation – thanks, buddy.",
        "Expensive lesson learned – again.",
        "The market said 'nope' – so I'm saying 'ouch'.",
        "SL triggered – my ego is in the ICU.",
        "Taking the loss like a champ... internally screaming.",
        "Stop loss hit – time to pretend this never happened.",
        "We got stopped out – but my therapy fund is growing.",
        "The chart betrayed me – classic Monday.",
        "SL activated – better than bagholding like a sucker.",
        "Loss booked – dignity preserved... barely.",
        "Stop loss did its job – my feelings did not.",
        "We took a hit – but we're still standing... kinda.",
        "Expensive tuition paid – trading school is rough.",
        "SL triggered – my portfolio is on a diet now.",
        "The market won this round – but I'm coming back swinging.",
        "Stop loss hit – time to update my resume.",
        "We got rekt – but at least we respected the rules.",
        "Loss accepted – ego denied.",
        "SL activated – better safe than broke.",
        "The dip was too deep – we drowned gracefully.",
        "Stop loss saved the day – my pride... not so much.",
        "We took the L – but we're still in the game.",
        "Expensive mistake – but character building.",
        "SL hit – time to blame the Fed, as always.",
        "The market kicked us – but we're getting back up.",
        "Loss booked – therapy appointment rescheduled.",
        "Stop loss triggered – my confidence is on vacation.",
        "We got stopped – but we're not stopping.",
        "SL activated – better than hoping and praying.",
        "The trade failed – but my discipline didn't.",
        "Loss taken – ego bruised but intact.",
        "Stop loss hit – time to reset and reload.",
        "We ate the L – but we're still hungry for wins.",
        "Expensive lesson – but worth it... maybe.",
        "SL triggered – my portfolio is now on life support.",
        "The market said 'no' – so we said 'bye'.",
        "Stop loss saved us from worse – silver lining.",
        "Loss accepted – next setup loading.",
        "SL hit – but we're still legends in our own minds.",
        "We took the hit – but we're still here.",
        "Stop loss did its job – my feelings are on strike.",
        "Expensive education – trading degree pending.",
        "SL activated – dignity intact... mostly.",
        "The trade died – long live the next trade.",
        "Loss booked – time to move on.",
        "Stop loss hit – but my spirit is unbreakable.",
        "We got rekt – but we're still fabulous."
    ],
    'HOLD': [
        "Holding like a boss – patience is my superpower.",
        "Doing absolutely nothing – and nailing it.",
        "Zen mode activated – watching paint dry is more exciting.",
        "No signal, no trade – living the quiet life.",
        "Holding forever – diamond hands or diamond prison?",
        "The chart is thinking – I'm just here breathing.",
        "Patience level: expert – coffee level: critical.",
        "Sideways action – my favorite kind of torture.",
        "Holding because selling would be too logical.",
        "The market is sleeping – so am I... mentally.",
        "No moves – just vibes and existential dread.",
        "Waiting for the magic moment – or lunch, whichever comes first.",
        "HODL mode – my hands are literally glued.",
        "The chart is drunk – I'm sober and waiting.",
        "Patience is a virtue – I'm basically a saint.",
        "Holding like it's 2017 all over again.",
        "No trade = no loss = winning at life.",
        "Watching the chart like it's Netflix.",
        "Holding because FOMO is for amateurs.",
        "The setup isn't here yet – but my coffee is.",
        "Silent mode – golden hands activated.",
        "Waiting game – I'm the champion.",
        "No action – just pure, unadulterated boredom.",
        "Holding because selling is for weaklings.",
        "The market is testing my patience – it's winning.",
        "Zen trading – inner peace, outer chaos.",
        "No moves today – tomorrow maybe.",
        "Holding like a pro – or like a stubborn mule.",
        "The chart is teasing me – I'm not falling for it.",
        "Patience loading... 99% complete.",
        "Holding forever – or until I need rent money.",
        "No signal – just me and my thoughts.",
        "Waiting like a sniper – but with coffee instead of a rifle.",
        "Holding because hope is a strategy... right?",
        "The market is quiet – so am I.",
        "No trade – just existential crisis.",
        "Holding mode – my hands are tired but strong.",
        "Patience is key – I'm basically a monk.",
        "Waiting for the breakout – or the breakdown.",
        "No moves – just pure discipline.",
        "Holding because I'm too lazy to sell.",
        "The chart is boring – my life is exciting.",
        "Waiting game – I'm winning at losing.",
        "No action – just me being responsible.",
        "Holding like a legend – or a bagholder.",
        "Patience level: god tier.",
        "The market is sleeping – sweet dreams.",
        "No signal – time for a nap.",
        "Holding forever – because why not?",
        "Zen mode – inner peace, portfolio pain."
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
def play_alert(action, symbol='EURUSD'):
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
        symbol = data.get('symbol', 'EURUSD').upper()
        
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
        print("  🔊 NOVA SOUND ENGINE - Edge-TTS Neural Voices")
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