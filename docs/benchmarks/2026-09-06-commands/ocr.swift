// 실제 화면의 문자열과 위치를 읽는 검사. 성능 측정과 분리해서 실행한다.
import Foundation
import Vision
import ImageIO
var output: [String: [[String: Any]]] = [:]
for path in CommandLine.arguments.dropFirst() {
let url = URL(fileURLWithPath: path)
let source = CGImageSourceCreateWithURL(url as CFURL, nil)!
let image = CGImageSourceCreateImageAtIndex(source, 0, nil)!
let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["en-US"]
request.usesLanguageCorrection = false
try VNImageRequestHandler(cgImage: image).perform([request])
let rows: [[String: Any]] = (request.results ?? []).compactMap { result in
  guard let text = result.topCandidates(1).first else { return nil }
  let box = result.boundingBox
  return ["text": text.string, "confidence": text.confidence,
          "x": box.minX, "y": box.minY, "width": box.width, "height": box.height]
}
output[url.lastPathComponent] = rows
}
let data = try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys])
print(String(data: data, encoding: .utf8)!)
