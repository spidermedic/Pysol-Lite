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
    ("restart", "arrow-counter-clockwise"),
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
    ("gotobookmark", "bookmark-simple-fill"),
]
let sizes: [(String, Int)] = [("small", 24), ("large", 32), ("xlarge", 48)]
let src = CommandLine.arguments[1]
let out = CommandLine.arguments[2]

func render(_ file: String, px: Int, white: Bool) -> Data? {
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
    let box = side * 0.92
    svg.draw(in: NSRect(x: (side - box) / 2, y: (side - box) / 2,
                        width: box, height: box))
    (white ? NSColor.white : NSColor.black).set()
    NSRect(x: 0, y: 0, width: side, height: side).fill(using: .sourceAtop)
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
            guard let data = render("\(src)/\(file).svg", px: px, white: white)
            else { print("cannot render", file); exit(1) }
            try! data.write(to: URL(fileURLWithPath: "\(dir)/\(name).png"))
        }
    }
}
print("done")
