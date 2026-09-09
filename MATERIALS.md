# Motif Moments Photobooth Materials Guide

## Recommended computer

Deploy Motif Moments on a small Windows x86 PC—not an Orange Pi, Raspberry Pi, or ESP32.

| Option | Recommendation | Suitable for |
|---|---|---|
| Intel N100/N150 mini PC, 16 GB RAM, 512 GB NVMe | Minimum recommended | Current photo capture, collage processing, printing, and QR uploads |
| Ryzen 5 5500U/5560U/5600U mini PC, 16 GB RAM, 512 GB NVMe | Best overall | Faster processing, future lightweight ML, and better long-term headroom |
| Raspberry Pi 5 8 GB | Experimentation only | Requires Linux camera/printer validation, active cooling, and preferably NVMe |
| Orange Pi 5 | Avoid for deployment | More OS and driver maintenance than Raspberry Pi |
| ESP32 | Peripheral controller only | Bill acceptor pulses, lights, buttons, and sensors—not the main application |

Purchase a Ryzen 5 mini PC if the price is within approximately ₱5,000–₱8,000 of an N100 system. Otherwise, an N100/N150 with 16 GB RAM is sufficient for the current original-filter collages and Supabase uploads.

Stay with Windows 11 because the current installation, printer workflow, `pywin32`, and digiCamControl path are already Windows-oriented. digiCamControl supports many Canon and Nikon cameras over USB. See the [supported camera list](https://digicamcontrol.com/cameras).

A Raspberry Pi 5 is capable, but it requires a 27 W supply and active cooling under sustained load. Once cooling, NVMe storage, a case, and driver validation are included, it offers little advantage for this deployment. See the [Raspberry Pi 5 specifications](https://www.raspberrypi.com/products/raspberry-pi-5/).

## Touchscreen recommendation

The practical budget choice is the [ViewPlus SX-156](https://www.viewplusph.com/products/sx-156):

- 15.6-inch IPS touchscreen
- 1920×1080 resolution
- Mini HDMI and USB-C inputs
- Approximately ₱9,600 from ViewPlus Philippines
- Local 18-month warranty

Before buying, confirm that touch works through a separate USB cable while video uses Mini HDMI. Also determine how it will be secured—the portable enclosure may require a retaining bezel instead of a normal monitor arm.

For a permanent unattended booth, a 21.5–24-inch VESA touchscreen is better but significantly more expensive. The 15.6-inch ViewPlus is suitable for the first booth, and the interface already supports 1920×1080 and 1280×720.

Avoid displays that:

- Only accept USB-C DisplayPort video
- Do not support separate HDMI video and USB touch
- Have no Windows HID touch support
- Are below 1080p
- Cannot be secured into the enclosure

## Construction materials

### Computer and controls

- Ryzen 5 or Intel N100/N150 mini PC
- 16 GB RAM
- 512 GB NVMe SSD
- Windows 11
- 15.6-inch 1080p capacitive touchscreen
- Powered USB 3 hub with individually switched ports
- Short HDMI-to-Mini-HDMI cable
- USB cable for touchscreen input
- Wired Ethernet cable
- Wi-Fi connection as backup
- Small keyboard and mouse stored in the operator compartment
- Lockable power/reset access
- Optional ESP32 or Arduino for the bill acceptor, illuminated buttons, and status lights

Use wired Ethernet where available. The booth can capture locally without internet, but Supabase QR delivery requires connectivity.

### Camera

For the prototype:

- Existing USB webcam, or Logitech C920/C922
- Adjustable camera bracket
- Tripod ball head
- USB extension cable
- Ferrite clips for longer USB cables

The Logitech C920 provides UVC USB support, autofocus, a 78° diagonal field of view, and 1080p at 30 fps. It is adequate for testing but not ideal for premium prints. See the [Logitech C920 specifications](https://support.logi.com/hc/en-001/articles/360023307294-C920-Technical-Specifications).

For production quality:

- Used Canon EOS 200D, 250D, M50, M50 II, or another supported camera
- Lens providing approximately a 24–35 mm full-frame-equivalent view
- Dummy battery/AC adapter
- Reliable USB data cable
- Camera safety tether
- Manual exposure and white balance
- Spare memory card even when tethering

Test the exact camera with the software before purchasing multiple units.

### Lighting

Use two lights instead of relying on one ring light:

- Two dimmable LED panels or softboxes
- CRI 95 or better
- Adjustable 3200–5600 K color temperature
- Diffusion material
- Wall, ceiling, or extrusion mounts
- Optional small front fill light
- White or silver reflector

Suggested placement:

- Main light 30–45° to one side
- Fill light on the opposite side at lower brightness
- Lights slightly above eye level
- Camera centred around eye level

### Curtains and backdrop

Blackout curtains are suitable for the outer booth walls because they control ambient light and provide privacy. Use a separate inner photographic backdrop.

Recommended combination:

- Flame-retardant black blackout curtains for the booth sides and entrance
- Matte cream, warm white, light gray, or pastel inner backdrop
- Ceiling-mounted curtain tracks or sturdy backdrop stands
- Curtain weights or Velcro at the bottom
- Floor tape marking where guests should stand
- Washable neutral floor mat

Avoid shiny black curtains as the photographed background. They show folds, collect lint, and make the Korean-style images feel too dark.

Keep guests approximately 0.8–1.2 metres away from the backdrop to soften shadows. Leave ventilation openings and never let fabric touch lights, power supplies, or exhaust vents.

### Enclosure

- 20×20 or 20×40 aluminium extrusion, or 12–18 mm plywood
- Lockable rear/operator door
- Touchscreen retaining bezel
- Camera window with removable clear acrylic
- Printer output opening
- Ventilation slots
- Two quiet 120 mm exhaust fans
- Washable dust filters
- Cable glands and cable channels
- Rubber feet or locking caster wheels
- Anti-tip brackets or floor anchors
- Service shelf for the mini PC and powered USB hub
- Lockable cash-box compartment
- Rounded edge trim
- Removable access panels

Aluminium extrusion is easier to modify. Plywood is cheaper and can provide a more finished furniture-like appearance after painting or laminating.

### Printer

For testing and low-volume events:

- Canon SELPHY CP1500
- RP-108 or equivalent 4×6 media
- Spare paper cassette
- Dedicated power adapter

The SELPHY CP1500 is a compact dye-sublimation printer that produces 4×6 prints in approximately 41 seconds, but its cassette holds only 18 sheets. See the [Canon Philippines specifications](https://ph.canon/en/consumer/selphy-cp1500/black/brochure).

For unattended commercial operation:

- DNP DS-RX1HS
- Spare media roll
- Sturdy ventilated printer shelf
- Large accessible output slot

The DS-RX1HS is better for paid deployment: approximately 12.4 seconds per 4×6 print and 700 prints per media set. See the [DNP DS-RX1HS specifications](https://www.dnpphoto.com/products/printers/rx1hs).

Use the SELPHY during software development, then upgrade before placing the booth somewhere with sustained customer traffic.

### Electrical and reliability

- UPS rated around 800–1200 VA
- Surge-protected power strip
- Main illuminated power switch
- Separate fused 12 V supply for the bill acceptor
- Separate regulated supplies for lights and computer
- Opto-isolated bill acceptor interface
- Inline fuses
- Proper grounding
- Cable labels
- Fire extinguisher nearby
- Emergency-accessible power cutoff
- Spare HDMI, USB, and power cables

Do not power lights or the bill acceptor from the computer's USB ports.

### Payment hardware

When the TB74 is qualified:

- TB74/TB74B with Philippine banknote firmware
- Official wiring harness
- Regulated 12 V supply
- Opto-isolated pulse input board
- ESP32 or Arduino controller
- USB serial interface
- Inline fuse
- Lockable steel cash box
- Service/inhibit switch
- Jam-access panel

The ESP32 belongs between the bill acceptor and backend; it should not run Motif Moments itself.

## Recommended first build

- Ryzen 5 5560U/5600U mini PC with 16 GB RAM, 512 GB NVMe, and Windows 11
- ViewPlus SX-156 touchscreen
- Existing webcam initially, followed by a used supported Canon camera
- Two CRI-95 LED panels
- Canon SELPHY CP1500 for testing
- Blackout-curtain outer walls with a cream inner backdrop
- Aluminium-extrusion or plywood enclosure
- Powered USB hub
- 1000 VA UPS
- Wired Ethernet
- TB74 hardware installed only after electrical qualification

This provides an inexpensive prototype without choosing hardware that must immediately be replaced. The printer is the sensible component to upgrade once customer volume justifies a DNP unit.
