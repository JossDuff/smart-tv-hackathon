# Smart TV hackathon: setup, lab TV, and findings

Handoff notes, last updated 2026-10-19. Everything below was verified on the TV itself
(camera snapshots), from packet captures on the testbed, or by probing the testbed CLI,
except where marked "unverified". Evidence files live in `handoff/`.

## 0. Project context

- **Hackathon theme: privacy.** The goal is to explore the privacy violations that smart
  TVs commit, e.g. what they phone home, automatic content recognition (ACR), personalized
  ads. The deliverable is expected to be a findings report or a dashboard showing where
  each TV sends data, which demos well.
- The work is done through a remote IoT lab testbed (`mrg-iot` CLI), not a TV in the room.
  You drive the TV over an IR blaster and watch it through a ceiling camera.
- **This is authorized security/privacy research** on a lab testbed built for exactly this.
- Workstation: Fedora (kernel 7.0.12-200.fc44.x86_64), zsh, i3 window manager, Wireshark
  installed. Repo lives at `/home/joss/dev/smart-tv-hackathon`.

## 1. Device identity

| Field | Value | Source |
|---|---|---|
| Manufacturer | Hisense | mDNS TXT `manufacturer=Hisense`, `integrator=Hisense` |
| Model | **32Q4SV** (32-inch QLED, Hisense "Q4" series; sold in Canada as 32QD4SV) | mDNS TXT `model=32Q4SV` |
| OS | **VIDAA** (Hisense's Linux-based smart TV OS) | Home screen UI, VIDAA branding, VIDAA Home app tile |
| Software Version | **V01.09.61Q.Q0723** | Settings > Support > About |
| Extended Version | X0004.W01.Y01.J01 | About page |
| Minor Version | Q.Q0723.9.61.00-b20260722q (firmware build dated 2026-07-22) | About page |
| AirPlay firmware string | fv=p20.09.61.260723, srcvers=377.40.00 | mDNS TXT |
| Serial Number | 32G25518SH00758 | About page; matches mDNS `serialNumber` |
| Device ID | 002003039003001248000125jkm3x4qhrg3etudpsw5yoml2o6jj7fib (camera read; verify) | About page |
| Netflix ESN | HISETVN2470000000000000000000000000009157131 (camera read, zero count approximate) | About page |
| Service Code | 00200303900300124800012520251229033 2Q40SUV_01 (camera read; the "...Q40SUV_01" tail looks like an internal variant code, not the retail model) | About page |
| Support URL / phone | https://www.hisense-usa.com/support, 1-888-935-8880 | About page (US firmware region) |
| TV name | "Living Room TV" | Settings > Connection > TV Name |
| Power draw | ~26 W idle on home screen | `get_power_consumption` |
| Advertising ID | 1e0392b0-77c5-aad4-5d7a-e6772ca... (prefix only) | System > Advanced Settings > Personalized Ads |

The About page does **not** print a model name. The model only shows up on the network
(AirPlay mDNS record). Both QR codes on the About and Product Registration pages are too
dense to decode from the lab camera. The Product Registration page is just a QR code
pointing to hisense-usa.com/support/register; it carries no extra on-screen info.

## 2. Network identity

| Field | Value |
|---|---|
| Testbed device name | `s-hisensetv-2` (NOT `s-hisense-2`) |
| VLAN | 2233 |
| TV IP | 172.30.105.3 (gateway 172.30.105.1) |
| MAC (Ethernet/Wi-Fi) | 74:d0:82:63:c8:32 |
| mDNS hostname | smarttv-74d08263c832.local |
| AirPlay device id / pi | CA:06:CE:2D:C1:2A (separate id used only by AirPlay) |
| AirPlay public key (pk) | d55eb15411b41bd2416e89b5ecd568cd0bad98d7f4f6e9fec6fe633747cc9963 |
| UPnP/DLNA | MediaRenderer:1 (AVTransport, ConnectionManager, RenderingControl) at `http://172.30.105.3:18400/MediaServer/rendererdevicedesc.xml`, UUID 8e90ee5d-cbef-11f1-b9cb-222031676aa3 |
| SSDP Server header | `Platform 1.0 His/1.0 UPnP/1.0 DLNADOC/1.50` |
| Camera | h-camera-5 |

Services seen advertised: `_airplay._tcp` (AirPlay On, "Require Code: First Time Only"),
UPnP MediaRenderer on TCP 18400. Hisense VIDAA TVs normally also run the MQTT remote
protocol on TCP 36669 (unverified here; a short capture saw nothing on that port).

Your laptop has **no route** to 172.30.105.0/24 (`ip route get 172.30.105.3` goes out your
Wi-Fi default gateway, not the lab). Direct `curl` to the TV fails. All network observation
must go through `mrg-iot stream capture`, which runs tcpdump on the lab side.

## 3. Testbed (mrg-iot) cheat sheet

Experiment is already set up (project `ioth`, experiment `iothhvqu`, realization `realiot`).
Every command opens its own SSH session through the experiment's xdc host, so each call
costs a few seconds. Session state is under `~/.mrg-iot/`.

```
mrg-iot devices list                 # shows s-hisensetv-2
mrg-iot devices list --available     # free devices across the lab
mrg-iot devices info                 # IP, MAC, VLAN, camera for your device
mrg-iot cmd run "s-hisensetv-2 commands"            # list device commands
mrg-iot cmd run "s-hisensetv-2 send_ir <button>"
mrg-iot cmd run "s-hisensetv-2 hold_ir <button> <secs>"
mrg-iot cmd run "s-hisensetv-2 ir_cmds"             # list IR buttons
mrg-iot cmd run "s-hisensetv-2 get_power_consumption"
mrg-iot cmd run "s-hisensetv-2 power_off" / power_on            # MAINS RELAY, hard cut
mrg-iot cmd run "s-hisensetv-2 power_by_timing on 1 off 1 on"   # scripted power sequence
mrg-iot cmd run "s-hisensetv-2 start_streaming <file>" / stop_streaming  # file -> HDMI2
mrg-iot cmd run "s-hisensetv-2 start_capture" / end_capture     # camera recording
mrg-iot stream push <file|url|webcam:N> -d s-hisensetv-2 --loop # laptop -> HDMI, accepts URLs
mrg-iot stream url                   # prints an rtsp:// URL for the camera
mrg-iot stream capture -f "<bpf>" -w out.pcap       # lab-side tcpdump; Ctrl-C or run bg w/ timeout
mrg-iot file list / upload / download / remove      # files in the experiment dir
mrg-iot cmd shell                    # interactive prompt (help, exp devices, exp cred, <dev> <cmd>)
mrg-iot cmd ctl                      # prompt from inside the xdc (no login/tunnel)
```

Full device command set: `power_on`, `power_off`, `power_by_timing`,
`get_power_consumption`, `start_capture`, `end_capture`, `send_ir`, `hold_ir`, `ir_cmds`,
`start_streaming`, `stop_streaming`. There is NO shell/exec command on the TV and no HTTP
fetch; the device cannot be made to run arbitrary code through the testbed.

IR buttons: power, input, home, back, up, down, left, right, accept (= ok/select/enter),
menu, play, pause, ch_up, ch_down, digits 0-9. NOT available: volume, mute, Netflix
shortcut, colour buttons.

**Camera snapshots:** `handoff/snap.sh <name>` saves `handoff/snaps/<name>.jpg` from the
RTSP stream (needs `ffmpeg`). Allow 5 to 10 s per IR press before snapshotting. ffmpeg
prints `Error constructing the frame RPS` / `Could not find ref with POC` HEVC warnings on
these grabs; harmless, the JPEG still writes. To read small on-screen text, crop and
upscale, e.g. `ffmpeg -i about.jpg -vf "crop=1400:600:600:470,scale=2800:1200:flags=lanczos" crop.jpg`.

## 4. VIDAA UI map (as observed)

- **Home screen**: banner at top (focus lands here after `home`), "Recent" and
  "Recommended For You" rows, app row (TV Channels, Netflix, Prime Video, Disney+,
  Apple TV, HBO Max, YouTube, Kids, Paramount+, Peacock, VIDAA Home, ...), inputs row.
  A rotating ad banner and a full-motion video ad with a QR code appear on the home screen
  (itself a privacy talking point).
- **Inputs row** (wraps around): HDMI1, AV, Content Sharing (DLNA), Music Sharing, Live TV,
  HDMI2 (has signal; the stream-to-HDMI box is on HDMI2), AirPlay, Screen Sharing (Miracast).
- **Sidebar** (press `left` from the banner, or up+left+left from the input row): Account,
  Search, Kids, Gaming, Notification, Settings. Focus usually lands on Settings; `accept`.
- **Settings categories** (top to bottom): Picture, Sound, Connection, Channel,
  Accessibility, System, Support. Focus starts on Picture; `down` x6 then `accept` reaches
  Support.
- **Support**: About, System Update, Product Registration, E-Manual, Self Diagnosis,
  Disclaimer and Privacy, Reset to Factory Default. About is first.
- **Connection**: TV Name, Network, AirPlay and HomeKit, Casting and Sharing, HDMI & CEC,
  Bluetooth, Karaoke Mode, Mobile App Download.
- **AirPlay and Apple Home** page: AirPlay toggle (On), Require Code (First Time Only),
  Subtitles and Captioning, About AirPlay, Reset Paired Devices, Apple Home Set Up.
  Toggling AirPlay off/on forces a fresh mDNS announcement (useful for captures).
- **System**: Time, Timers, Language and Location, Voice Service, Parental Control,
  Application Manager, Advanced Settings.
- **System > Advanced Settings** (10 items, list wraps): includes Auto Init Mode ON,
  Fast Power On ON, Power On Mode Standby, ... , **Personalized Ads ON**,
  **Personalized Recommendation ON**. The Personalized Ads submenu shows the advertising ID
  (prefix `1e0392b0-77c5-aad4-5d7a-e6772ca`). These two toggles are the obvious privacy
  controls on this set.
- **Not yet inspected**: Support > Disclaimer and Privacy (likely the ACR / "Viewing
  Information Services" toggle and the privacy policy text), Connection > Network info page,
  Account page, E-Manual, Self Diagnosis, Voice Service, Application Manager.

Quirks: `input` does not open a picker, it just advances along the input row. `menu` does
nothing on the home screen. Pressing `accept` on a dialog's OK sometimes drops focus back
to the Settings category list rather than the sub-menu you came from. A
"Screen Sharing: exit the app?" dialog needs `accept` on OK. Lists wrap, so count presses.

## 5. Upload and HDMI-streaming path (probed; privacy-injection vector)

A previous session probed the `file upload` + `start_streaming` path. Findings:

- **Upload has no validation.** Every file type tried (shell script, fake ELF, HTML, text,
  raw bytes) was accepted and stored in the experiment's `uploads/` dir. No extension or
  content check.
- **Stored is not executed.** Nothing runs an uploaded file as code, on the TV or the
  testbed. The only thing that "runs" an upload is `start_streaming`, which feeds the file
  to an ffmpeg/VLC-class pipeline on the stream-to-HDMI box and pushes decoded video over
  HDMI into the TV. "Executable" here means "decodable media", not code.
- **Container support is broad.** Plays: mp4, mkv, avi, mov, webm, ts, mp3. Rejected
  (non-media): html, elf, txt, bin. Two error strings map to two stages: "Video is not
  available. Ensure the file is uploaded" = existence check failed; "Failed to start
  streaming to HDMI" = found but not decodable.
- **Source path is NOT confined to `uploads/`.** Absolute paths and `../` traversal resolve
  on the streamer host (proven by streaming `../output/h-camera-5-capture.mp4`, the camera
  recording outside the uploads dir). `/etc/passwd` passed the existence check and only
  failed at decode. So the arg is not sandboxed, but you cannot read arbitrary file
  contents out over HDMI (non-media won't decode).
- **Limits:** `start_streaming` does not fetch URLs (only `mrg-iot stream push` does). The
  arg parser splits on whitespace and takes 0 or 1 argument, so filenames with spaces break
  and whitespace command injection is rejected.
- **Possible bug:** `file remove` returned "Removed" but the files still showed in
  `file list` afterward. Junk is wiped at experiment teardown regardless.
- **Why it matters for the privacy angle:** this upload-and-stream path is the "inject
  content onto the screen" vector. It is HDMI playback simulating an external source
  (console, Blu-ray). It is the right tool for showing the TV fingerprinting HDMI content
  via ACR. It is NOT a route to run code on the TV firmware.

## 6. Repo contents

- `clip.mp4` (~31 MB, ISO MP4): a real video clip, usable as an HDMI test source for ACR.
- `uploadtest/`: artifacts left from the upload probe above. `vid.mkv|avi|mov|webm|ts|mp3`
  are generated test clips (handy HDMI sources). `test.sh|elf|html|bin|txt`, `dotdot.txt`,
  `trav.txt`, `esc.txt`, `pwn.txt`, `weird name.mp4` were upload/traversal probes (benign).
- `snaps/`: camera snapshots from this session's navigation.
- `handoff/`: evidence for this write-up (see below).
- `TV_INFO.md`: this file.

## 7. Evidence files (`handoff/`)

- `about_page.jpg`, `about_page_crop.jpg`: Settings > Support > About, full frame + upscaled
  crop of the text block.
- `support_menu.jpg`: the Support sub-menu.
- `tv_ssdp.pcap`: 75 s capture of SSDP NOTIFY packets from the TV (UPnP MediaRenderer).
- `tv_mdns_ssdp.pcap`: 200 s capture of mDNS + SSDP, includes the AirPlay TXT record.
- `airplay_txt_record.txt`: the parsed AirPlay TXT key/value pairs.
- `snap.sh`: camera snapshot helper (edited to save beside itself in `handoff/snaps/`).

Re-parse the model/serial from the mDNS record with:
```
tshark -r handoff/tv_mdns_ssdp.pcap -Y "mdns && ip.src==172.30.105.3" -T fields -e dns.txt
```

## 8. Open items / next ideas

- **Capture where the TV phones home.** Longer captures broken out by destination domain
  and company make the best demo. Grep for the advertising ID prefix `1e0392b0-77c5` and the
  serial `32G25518SH00758` to see which cloud endpoints receive them.
- **ACR demo.** Stream known content over HDMI (`clip.mp4` via `start_streaming` or
  `stream push`) and capture what the TV reports to Hisense/ACR partners. Support >
  Disclaimer and Privacy likely holds the "Viewing Information Services" (ACR) toggle;
  compare traffic with it on vs off.
- **System Update capture.** Watch traffic during Support > System Update to see what the
  TV tells Hisense's update servers about itself.
- **UPnP description XML.** Fetch `http://172.30.105.3:18400/MediaServer/rendererdevicedesc.xml`
  from inside the lab (needs an SSH hop to the xdc host; the mrg-iot CLI already tunnels
  through it). Should contain modelName, modelNumber, friendlyName.
- **MQTT remote (TCP 36669).** Check whether the VIDAA remote-control service is reachable
  from the lab network.
- **Cold-boot traffic.** Use `power_off`/`power_on` (mains relay) to capture what the TV
  does on a fresh boot.

## 9. Important note for whoever picks this up

As of this handoff, **another model/session is actively driving the TV over IR.** Do not
send TV commands (`send_ir`, `power_*`, `start_streaming`, etc.) until you confirm the TV
is free, or you will fight over the remote. Read-only testbed calls (`devices info`,
`stream capture`, `stream url`, `file list`) are safe to run alongside.
