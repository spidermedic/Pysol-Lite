// Renders the toolbar icons from the Phosphor SVG files to PNG files.
//
//   swiftc -O scripts/render_toolbar_icons.swift -o /tmp/render_toolbar_icons
//   /tmp/render_toolbar_icons <dir with the .svg files> \
//       data/images/toolbar/phosphor
//
// Needs the Phosphor icons named in `icons` below ("regular" weight, plus one "fill") (from
// https://github.com/phosphor-icons/core, MIT licence). Writes
// <out>/{small,large,xlarge}/<name>.png (black, for light interfaces) and
// <out>/light/{small,large,xlarge}/<name>.png (white, for dark ones).
// Must run on macOS.
import AppKit

// toolbar button name -> Phosphor icon file name
let icons: [(String, String)] = [
    ("new", "file-plus"),
    ("restart", "clock-counter-clockwise"),
    ("open", "folder-open"),
    ("save", "floppy-disk"),
    ("undo", "arrow-u-up-left"),
    ("redo", "arrow-u-up-right"),
    ("autodrop", "arrow-line-down"),
    ("shuffle", "shuffle"),
    ("hint", "lightbulb"),
    ("pause", "pause"),
    ("rules", "book-open"),
    ("bookmark", "bookmark-simple"),
    ("bookmark_on", "bookmark-simple-fill"),
    ("favorite", "heart"),
    ("favorite_on", "heart-fill"),
    ("menu", "list"),            // the Android menu button
]
// "on" icons are coloured instead of black/white: name -> (light UI, dark UI)
func hex(_ v: Int) -> NSColor {
    return NSColor(deviceRed: CGFloat((v >> 16) & 255) / 255,
                   green: CGFloat((v >> 8) & 255) / 255,
                   blue: CGFloat(v & 255) / 255, alpha: 1)
}
let onColors: [String: (NSColor, NSColor)] = [
    "favorite_on": (hex(0xE0343B), hex(0xFF5A5F)),   // red
    "bookmark_on": (hex(0xF0B000), hex(0xFFD43B)),   // yellow
]
let sizes: [(String, Int)] = [("small", 24), ("large", 32), ("xlarge", 48)]
let src = CommandLine.arguments[1]
let out = CommandLine.arguments[2]

func render(_ file: String, px: Int, white: Bool, color: NSColor? = nil,
            badge: Bool = false) -> Data? {
    guard let svg = NSImage(contentsOfFile: file) else { return nil }
    let scale = 2   // draw at 2x, then let the PNG carry px x px pixels
    let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: px * scale, pixelsHigh: px * scale,
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSGraphicsContext.current?.imageInterpolation = .high
    let side = CGFloat(px * scale)
    if badge {
        // White disc with a thin grey rim, so the icon stays visible on any
        // table colour (the glyph is blue or red, like the table background).
        let d = side * 0.96
        let disc = NSBezierPath(ovalIn: NSRect(x: (side - d) / 2, y: (side - d) / 2,
                                               width: d, height: d))
        NSColor(deviceWhite: 1, alpha: 0.94).setFill()
        disc.fill()
        NSColor(deviceWhite: 0.35, alpha: 0.9).setStroke()
        disc.lineWidth = side * 0.03
        disc.stroke()
    }
    if badge {
        // Draw the glyph on its own layer and tint only that, not the badge.
        let box = side * 0.66
        let glyph = NSImage(size: NSSize(width: side, height: side))
        glyph.lockFocus()
        svg.draw(in: NSRect(x: (side - box) / 2, y: (side - box) / 2,
                            width: box, height: box))
        (color ?? NSColor.black).set()
        NSRect(x: 0, y: 0, width: side, height: side).fill(using: .sourceAtop)
        glyph.unlockFocus()
        glyph.draw(in: NSRect(x: 0, y: 0, width: side, height: side))
    } else {
        let box = side * 0.92
        svg.draw(in: NSRect(x: (side - box) / 2, y: (side - box) / 2,
                            width: box, height: box))
        (color ?? (white ? NSColor.white : NSColor.black)).set()
        NSRect(x: 0, y: 0, width: side, height: side).fill(using: .sourceAtop)
    }
    NSGraphicsContext.restoreGraphicsState()
    // scale down to the final size with good quality
    let final = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: px, pixelsHigh: px,
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: final)
    NSGraphicsContext.current?.imageInterpolation = .high
    let big = NSImage(size: NSSize(width: side, height: side))
    big.addRepresentation(rep)
    big.draw(in: NSRect(x: 0, y: 0, width: px, height: px))
    NSGraphicsContext.restoreGraphicsState()
    return final.representation(using: .png, properties: [:])
}

let fm = FileManager.default
for white in [false, true] {
    for (sizeName, px) in sizes {
        let dir = white ? "\(out)/light/\(sizeName)" : "\(out)/\(sizeName)"
        try! fm.createDirectory(atPath: dir, withIntermediateDirectories: true)
        for (name, file) in icons {
            let tint = onColors[name].map { white ? $0.1 : $0.0 }
            guard let data = render("\(src)/\(file).svg", px: px, white: white,
                                    color: tint)
            else { print("cannot render", file); exit(1) }
            try! data.write(to: URL(fileURLWithPath: "\(dir)/\(name).png"))
        }
    }
}

// Dialog icons (coloured, one fixed size) go next to the toolbar folder:
// <out>/../../dialog/phosphor
let imagesRoot = URL(fileURLWithPath: out).deletingLastPathComponent()
    .deletingLastPathComponent().path
let others: [(String, Int, [(String, String, NSColor)])] = [
    // Drawn on the table over the Talon: redeal arrows and "no more redeals".
    ("redealicons/modern", 48, [
        ("redeal", "arrows-clockwise", hex(0x2F7DE1)),
        ("stopsign", "x-circle", hex(0xE0343B)),
    ]),
    ("dialog/phosphor", 48, [
        ("error", "x-circle-fill", hex(0xE0343B)),
        ("info", "info-fill", hex(0x2F7DE1)),
        ("question", "question-fill", hex(0x1F9BE0)),
        ("warning", "warning-fill", hex(0xF0A000)),
    ]),
]
for (subdir, px, items) in others {
    let dir = "\(imagesRoot)/\(subdir)"
    try! fm.createDirectory(atPath: dir, withIntermediateDirectories: true)
    for (name, file, color) in items {
        guard let data = render("\(src)/\(file).svg", px: px, white: false,
                                color: color, badge: subdir.hasPrefix("redealicons"))
        else { print("cannot render", file); exit(1) }
        try! data.write(to: URL(fileURLWithPath: "\(dir)/\(name).png"))
    }
}
print("done")
