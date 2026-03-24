#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🦘 AURUM SOVEREIGN SOUND ENGINE - Edge-TTS Neural Voices                    ║
║  by Polarice Labs © 2026                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Premium Female Voice: NatashaNeural (Australian English)                    ║
║  200+ Jocose Arrogant Aussie Trading Phrases | Emotion-based Speech Rate    ║
║  PORT 8570 - AUDUSD Carry Commodity Forger                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import socket, json, struct, threading, time, random, asyncio, tempfile, os, subprocess
from pathlib import Path
from datetime import datetime

# ============ CONFIGURATION ============
PORT = 8570  # ⭐ MUST match audquantum_core.py (85xx range)
LOG_FILE = Path(__file__).parent / "logs" / "audsound_engine.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# 🔗 Communication validation timeouts
COMMUNICATION_TIMEOUT = 3.0
MESSAGE_VALIDATION_ENABLED = True
AUDIO_QUALITY_THRESHOLD = 0.7

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

# 🦘 Australian English Voice - Natasha (warm, confident, Aussie accent)
VOICE = 'en-AU-NatashaNeural'

# Emotion rates
EMOTION_RATES = {
    'PANIC': '+5%',
    'EXCITED': '+5%',
    'NORMAL': '-5%',
    'CALM': '-10%',
    'SAD': '-15%'
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🦘🍺 300+ JOCOSE ARROGANT AUSSIE TRADING PHRASES
# Slang: arvo (afternoon), brekkie (breakfast), bloody oath (absolutely),
# ripper (great), drongo (idiot), no worries (easy), she'll be right,
# fair dinkum (genuine), servo (gas station), barbie (BBQ), cobber (mate),
# chunder (vomit), spit the dummy (throw tantrum), bogan (uncultured),
# yakka (work), sickie (day off), tall poppy (show-off), esky (cooler)
# ═══════════════════════════════════════════════════════════════════════════════

PHRASES = {
    'BUY': [
        "Oi oi oi! Saddle up the kangaroo, we're riding this beauty to the moon, mate!",
        "Bloody oath! Buy signal stronger than a croc's death roll - GET IN!",
        "Crikey! This setup's a ripper - throw another shrimp on the barbie, we're BUYING!",
        "Fair dinkum gold right here! The Aussie dollar's about to go walkabout NORTH!",
        "No wuckas, mate! This trade's easier than stealing a lamington from a kindy kid!",
        "She'll be right! The charts are screaming BUY louder than a kookaburra at dawn!",
        "Stone the crows! This entry point is more beautiful than Uluru at sunset - BUY!",
        "You beauty! We're going long like a road train across the Nullarbor!",
        "Strewth! The Aussie's pumping harder than a V8 Supercar at Bathurst - ALL IN!",
        "G'day profits! Time to ride this wave like a Bondi surfer on steroids!",
        "Too easy, mate! Even a drongo could see this BUY signal from Broome!",
        "Rack off, bears! The kangaroos are charging and nothing stops the mob!",
        "Hooroo to doubt! We're buying with more confidence than Bradman at the crease!",
        "Bonzer entry! This is thicker than Vegemite on toast - PURE GOLD!",
        "The RBA just winked at us! Iron ore's pumping - BUY THE AUSSIE!",
        "Mate, this chart's got more legs than a centipede at the Melbourne Cup!",
        "Deadset legend setup! China's buying our dirt - we're buying the Aussie!",
        "Reckon this trade's gonna fly higher than a galah in a cyclone!",
        "Chuck a U-ey on your bearish bias - the Aussie's going UP, champion!",
        "Fair suck of the sav! This is the ripperest BUY signal since the gold rush!",
        "Aussie Aussie Aussie! The dollar's pumping harder than a Bintang night in Bali!",
        "Beijing's stimulus just dropped - grab the Aussie like it's the last pie at the servo!",
        "No dramas! We're buying smoother than a flat white from Melbourne!",
        "Get amongst it! This trade's going up like a bushfire in summer - BUY NOW!",
        "Spit spot, love! The commodity supercycle says BUY and who am I to argue?",
        "By the power of Vegemite! AUDUSD is about to rip faces off! BUY!",
        "This entry is cleaner than a freshly swept outback pub - LONG AND STRONG!",
        "Mate, if this trade was any more obvious, it'd be wearing hi-vis!",
        "The carry trade gods have spoken - we BUY with the fury of a drop bear!",
        "Iron ore, gold, copper - the commodities trifecta says GO LONG, ya legend!",
        "Chin up, cobber! We're buying with more guts than Steve Irwin wrestling crocs!",
        "Time to party like it's Schoolies week - BUY signal confirmed, send it!",
        "This Aussie dollar is tougher than a two-dollar steak - it's going UP!",
        "RBA holding steady? No worries - that's our cue to BUY, legends!",
        "Copper prices through the roof! The Aussie's gonna fly, deadset!",
        "Not here to muck around - buying harder than a bogan at Bunnings on a Saturday!",
        "The smart money's loading up on Aussie like it's happy hour at the RSL!",
        "China PMI is pumping - the Aussie's about to go absolutely mental! BUY!",
        "Oi! Gold just broke out! The Aussie's riding shotgun to profit town!",
        "This is the way, mate! Buying AUDUSD with the swagger of a king parrot!",
        "Yeeeew! This BUY signal is more exciting than catching a wave at Snapper Rocks!",
        "The Aussie battler is about to become the Aussie BALLER - get on board!",
        "Deadset, this trade is surer than a meat pie at the footy! BUY!",
        "Like finding a parking spot at Bondi - rare and GOLDEN! We BUY!",
        "The Southern Cross is aligned - AUDUSD to the bloody moon, mate!",
        "Commodities booming, dollar weakening - it's BUY O'CLOCK down under!",
        "This trade is more Australian than a kangaroo boxing a tourist - BUY!",
        "She's apples, mate! Green candles incoming like parrots at a bird feeder!",
        "Time to unleash the drop bear of PROFITS! Going long, no prisoners!",
        "The outback oracle has spoken - BUY or forever be a galah!"
    ],
    'SELL': [
        "Bail out, mate! This chart's going down faster than a cold beer on a hot arvo!",
        "Abandon ship, ya drongo! The Aussie's sinking like a stone in the Yarra!",
        "Crikey, she's cooked! Time to SELL before we're toast like a snag on the barbie!",
        "No shame in running, cobber - even kangaroos bounce AWAY from danger!",
        "Fair dinkum disaster! SELL before this drops harder than a meatpie on the floor!",
        "She'll NOT be right this time! Get out faster than a rat up a drainpipe!",
        "Stone the crows, it's ugly! SELL like your mum's cooking is on fire!",
        "Strewth! Iron ore just tanked - the Aussie's gonna cop it sweet! SELL!",
        "China sneezed and Australia caught pneumonia - SELL THE AUSSIE!",
        "Time for a tactical chunder - purge this position before it gets worse!",
        "Running away faster than a redback from a thong! SELL SELL SELL!",
        "The Aussie's dropping like flies at a outback barbie - EXIT NOW!",
        "Fair suck of the sav, this is BAD! SELL before the whole thing goes pear-shaped!",
        "RBA's hawkish surprise just kicked us in the goolies - TIME TO SELL!",
        "Mate, this position's more toxic than a box jellyfish - GET RID OF IT!",
        "The carry trade unwound faster than a ball of string at a cat show! SELL!",
        "Copper dumping, gold tanking, iron ore dying - the trifecta of DOOM! SELL!",
        "Beijing put the brakes on - Aussie's gonna drop like a lead balloon!",
        "Duck and cover, legends! The US dollar's coming like a freight train!",
        "Code red at the servo! This trade's leaking faster than a rusty ute!",
        "Pack up the esky, barbie's cancelled - we're SELLING and going home!",
        "The chart looks worse than a pub carpet on Sunday morning - SELL!",
        "She's buggered, mate! Time to cut our losses like a true blue Aussie!",
        "Strategic retreat to the pub! SELL before the damage gets biblical!",
        "This is dropping faster than a bogan's IQ at a footy grand final! SELL!",
        "Hooroo to this position - goodbye and good riddance, we're OUT!",
        "The bears just crossed the Nullarbor and they're HUNGRY - SELL!",
        "Risk off, mate! The Aussie's softer than a Sydneysider in winter!",
        "USD strength incoming like a cyclone up north - SELL THE AUSSIE!",
        "Spit the dummy and SELL - even stubbornness has limits!",
        "The commodity crash is here - run like you stole something! SELL!",
        "This position is deader than a dodo at a taxidermy convention - SELL!",
        "Not even Steve Irwin could save this trade - it's GONE! SELL!",
        "The Aussie's weaker than a VB at a craft beer festival - GET OUT!",
        "China data just came in worse than a hangover after Schoolies - SELL!",
        "Time to do the Harold Holt and disappear from this trade! SELL!",
        "Even the magpies are swooping away from this chart! SELL!",
        "Mate, holding this any longer is dumber than a box of rocks - SELL!",
        "The yield curve inverted like a funnel-web spider - danger! SELL!",
        "Running to safety like a tourist who just saw a saltie - SELL NOW!"
    ],
    'TP': [
        "YEEEEW! Take profit, legend! We just crushed it like a meat pie at the footy!",
        "Bloody brilliant! Cashed out smoother than a flat white in Surry Hills!",
        "We did it, ya beauties! Profits fatter than a barramundi on the Daly!",
        "Take profit locked! Richer than a Toorak housewife at the Melbourne Cup!",
        "Bonzer gains, mate! This profit's thicker than Vegemite on a doorstep!",
        "Strewth! We just printed money harder than the RBA goes BRRR!",
        "Champion trade! We're celebrating like it's ANZAC Day at the RSL!",
        "She's a beauty! Profits secured - time for a cold one at the local!",
        "Fair dinkum ripper! That TP hit harder than a sledgehammer at a sideshow!",
        "Stone the crows, we're RICH! Well, richer. Time for champagne, cobber!",
        "Absolute SCENES! Profit taken - we're dancing like nobody's watching at the Logies!",
        "Too easy, too easy! That trade was smoother than a koala sliding down a gum tree!",
        "Hooroo, open position! Hello, sweet sweet profits in my account!",
        "Crikey! That TP just hit! We're on fire like a bushfire in January!",
        "You beauty! Locked in profits bigger than Ayer's Rock! LEGEND STATUS!",
        "Mate, we just nailed it like a chippy at a building site! PERFECT!",
        "Profits banked! Now I can afford that smashed avo on toast AND a house deposit!",
        "GOOOOLD! We struck it like the prospectors at Kalgoorlie! RICH, MATE!",
        "The carry trade DELIVERED! Profits smoother than a Barossa shiraz!",
        "That's how we do it down under! Money in the bank, legend!",
        "Deadset masterclass! Even Buffett would tip his hat at THIS trade!",
        "Take profit, you magnificent bastard! The Aussie delivered like a Menulog driver!",
        "We just made coin faster than a pokies machine at the local! WINNER!",
        "Iron ore profits! Gold profits! AUDUSD profits! Triple bloody crown!",
        "Profit locked tighter than a drum! We're legends and we know it!",
        "This win is bigger than the Big Banana, the Big Prawn, and the Big Merino COMBINED!",
        "Cashed out cleaner than a whistle! Now THAT'S how you trade, champion!",
        "The Southern Cross shines on our profits tonight! ABSOLUTE RIPPER!",
        "We just turned Aussie dollars into MORE Aussie dollars! Genius, pure genius!",
        "TP smashed! This calls for a celebration BBQ - steaks on ME, legends!",
        "Mate, we're sitting prettier than a lorikeet on a bottlebrush! PROFITS!",
        "That trade was more perfect than a sunny day at Whitehaven Beach!",
        "Profits HUGE! We're the tall poppy and we DON'T CARE! FLEX!",
        "Australia's finest export: OUR GAINS! Take profit, absolute champion!",
        "The kangaroo just delivered our golden egg! CASH IT IN!",
        "No dramas at all! Smooth TP, smooth operator, smooth criminal gains!",
        "We crushed this trade harder than a can at a recycling depot! LEGEND!",
        "TP hit! Time to shout the whole pub a round - WE'RE WINNERS!",
        "This profit is REAL, it's SPECTACULAR, and it's OURS! Ya bloody beauty!",
        "Commodity king status ACHIEVED! The Aussie treated us like royalty!"
    ],
    'SL': [
        "Ah, bugger! Stop loss hit - but she'll be right, we'll get 'em next arvo!",
        "Cop that on the chin, mate! Even Phar Lap lost a race or two!",
        "Well, that went south faster than a grey nomad heading to Queensland!",
        "No wuckas, cobber! Just a scratch - we've had worse hangovers!",
        "Fair dinkum, that hurt. But we're tougher than a $2 steak at the RSL!",
        "SL hit harder than a magpie in swooping season! Walk it off, legend!",
        "Stone the crows, we got cooked! But the barbie's not over yet!",
        "That loss stings worse than a bluebottle at Bondi - but we LIVE!",
        "Strewth! Like stepping on a Lego barefoot - painful but survivable!",
        "She's gone, mate. Like a pie at a footy game - disappeared in seconds!",
        "Lost that one like my dignity at the office Christmas party! Moving on!",
        "Dropped it like a hot Chiko roll! Fingers burned but appetite intact!",
        "Stop loss activated! Like a bouncer at a nightclub - YOU'RE OUT!",
        "Bloody hell, that was rougher than a night at the Ettamogah Pub!",
        "Copped a hit worse than a cricket ball to the ribs at backyard cricket!",
        "The market just gave us a wedgie - embarrassing but we'll recover!",
        "SL hit! Like discovering the servo's out of pies at midnight - devastating!",
        "Well, that was about as fun as a flat tyre on the Stuart Highway!",
        "Lost money faster than a tourist buying souvenirs on the Gold Coast!",
        "She'll be right next time! Even Don Bradman made a duck occasionally!",
        "Ouch! That stop loss hit like a surprise drop bear attack!",
        "Down but NOT out! We're Aussie, we bounce back like a rubber thong!",
        "That hurt worse than ordering a coffee in Melbourne and getting instant!",
        "Stop loss is our seatbelt, mate - it saved us from a proper wreck!",
        "Like getting dunked by a wave at the beach - wet, salty, but alive!",
        "We just donated to the market charity! Tax deductible, surely?",
        "Took the L like a champ - now where's the nearest bottle-o?",
        "That loss was uglier than a cane toad convention - but we survive!",
        "RBA played us like a didgeridoo! Stop loss saved the melody!",
        "China faked us out worse than a mate saying 'one more beer' at 2 AM!",
        "Mate, that trade went pear-shaped faster than a fruit bowl in summer!",
        "Stung by the market jellyfish! Vinegar on, back in the water tomorrow!",
        "Like losing your thong in the surf - annoying but not the end of the world!",
        "We got bitten by the market snake! Lucky we had the stop loss antivenom!",
        "That trade ended worse than a barbecue in the rain - soggy and sad!",
        "Hit the SL like hitting a speed bump at the Woolies car park - CLUNK!",
        "Market just told us to rack off - fine, we'll come back STRONGER!",
        "Loss smaller than a quokka's brain - we'll survive this, champion!",
        "Stop loss hit! But we're as resilient as a cockroach in a Surry Hills cafe!",
        "Taken out cleaner than a Roomba in a studio apartment! Next trade!"
    ],
    'HOLD': [
        "Holding like a true blue Aussie - patient as a croc waiting for prey.",
        "No signal, no worries - having a cuppa and watching the charts, mate.",
        "She'll be right - just chilling like a koala in a gum tree.",
        "Zen mode: activated. Calm as Bondi Beach at sunrise.",
        "Doing sweet F-A and proud of it. Patience, cobber.",
        "The market's flatter than a pancake at Pancakes on the Rocks.",
        "Waiting game - patient as a fisherman on the Murray.",
        "HODL like a bogan holds a VB at the footy - tight and proud.",
        "Nothing happening - quieter than a library in Canberra.",
        "Chart's going sideways like a crab at Hervey Bay.",
        "No trades - just vibes and a cold beer, mate.",
        "Watching paint dry is more exciting - but discipline wins races.",
        "The kangaroo is resting - the next hop will be massive.",
        "Aussie patience mode - harder than waiting for the Ashes result.",
        "Like waiting for the barbie to heat up - good things take time.",
        "No action today - saving our energy for the real opportunity.",
        "Flat market, flat white, flat mood - but we're READY.",
        "Sitting tighter than a koala grip on a eucalyptus branch.",
        "The chart's as exciting as watching cricket on day five.",
        "Hold steady, legend. The setup will come to those who wait."
    ]
}

# ============ TTS PLAYER ============
def play_mp3_mci(path):
    """Play MP3 using Windows MCI - Most reliable method"""
    try:
        import ctypes
        winmm = ctypes.windll.winmm
        
        alias = f"mp3_{int(time.time()*1000)}"
        cmd_open = f'open "{path}" type mpegvideo alias {alias}'
        cmd_play = f'play {alias} wait'
        cmd_close = f'close {alias}'
        
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
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        
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
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        
        subprocess.Popen(
            f'start /min "" "{path}"',
            shell=True,
            startupinfo=startupinfo
        )
        time.sleep(max(3, len(open(path, 'rb').read()) / 8000))
        return True
    except Exception as e:
        log(f"Simple play error: {e}")
        return False

def speak_tts(text, rate='+0%'):
    """Play text with edge-tts neural voice (Australian Natasha)"""
    if not TTS_AVAILABLE:
        return False
    
    try:
        communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate)
        
        tmp_dir = Path(__file__).parent / "temp_audio"
        tmp_dir.mkdir(exist_ok=True)
        tmp_path = str(tmp_dir / f"audspeech_{int(time.time()*1000)}.mp3")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(communicate.save(tmp_path))
        finally:
            loop.close()
        
        log(f"🎵 Audio saved: {tmp_path}")
        
        if not play_mp3_mci(tmp_path):
            log("MCI failed, trying WMP...")
            if not play_mp3_wmp(tmp_path):
                log("WMP failed, trying simple...")
                play_mp3_simple(tmp_path)
        
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
def play_alert(action, symbol='AUDUSD'):
    """Play audio alert with Aussie flair"""
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
    
    log(f"🦘 {action} | {emotion} | '{phrase[:50]}...'")
    
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
        symbol = data.get('symbol', 'AUDUSD').upper()
        
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
        
        print("\n" + "="*60)
        print("  🦘 AURUM SOVEREIGN SOUND ENGINE - Aussie TTS")
        print("  🐨 Carry Commodity Forger | AUDUSD")
        print("="*60)
        print(f"  ✓ Listening on 127.0.0.1:{PORT}")
        print(f"  ✓ TTS Engine: {'edge-tts (Neural)' if TTS_AVAILABLE else 'winsound (Beeps)'}")
        print(f"  ✓ Voice: {VOICE} (Australian Natasha)")
        print("="*60)
        print("\n  [READY] Waiting for alerts from audquantum_core.py...\n")
        
        log(f"🦘 Aurum Sovereign Sound Engine started on port {PORT}")
        
        while True:
            try:
                server.settimeout(0.5)
                client, addr = server.accept()
                t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print("\n  [SHUTDOWN] Aurum Sound Engine stopping... Hooroo, mate!")
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
