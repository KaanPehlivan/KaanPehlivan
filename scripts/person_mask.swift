// One-time helper (macOS): writes a person mask PNG so dark hair stays visible in the ASCII portrait.
// Usage: swift scripts/person_mask.swift <photo.jpg> <mask.png>
import AppKit
import CoreImage
import Vision

let args = CommandLine.arguments
let image = CIImage(contentsOf: URL(fileURLWithPath: args[1]))!
let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
try VNImageRequestHandler(ciImage: image).perform([request])
let mask = CIImage(cvPixelBuffer: request.results!.first!.pixelBuffer)
let scaled = mask.transformed(by: CGAffineTransform(scaleX: image.extent.width / mask.extent.width,
                                                    y: image.extent.height / mask.extent.height))
let rep = NSBitmapImageRep(ciImage: scaled)
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2]))
