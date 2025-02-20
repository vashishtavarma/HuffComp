from flask import Flask, render_template, request, send_file
import os
import heapq
from collections import defaultdict

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def buildHuffmanTree(freqTable):
    priorityQueue = [HuffmanNode(char, freq) for char, freq in freqTable.items()]
    heapq.heapify(priorityQueue)

    while len(priorityQueue) > 1:
        leftNode = heapq.heappop(priorityQueue)
        rightNode = heapq.heappop(priorityQueue)
        mergedNode = HuffmanNode(None, leftNode.freq + rightNode.freq)
        mergedNode.left = leftNode
        mergedNode.right = rightNode
        heapq.heappush(priorityQueue, mergedNode)

    return priorityQueue[0]

def generateHuffmanCodes(treeNode, currentCode="", codeDictionary=None):
    if codeDictionary is None:
        codeDictionary = {}
    if treeNode:
        if treeNode.char is not None:
            codeDictionary[treeNode.char] = currentCode
        generateHuffmanCodes(treeNode.left, currentCode + "0", codeDictionary)
        generateHuffmanCodes(treeNode.right, currentCode + "1", codeDictionary)
    return codeDictionary

def encodeInputData(inputData, huffmanCodes):
    return ''.join(huffmanCodes[byte] for byte in inputData)

def decodeEncodedData(encodedData, tRoot):
    decodedOutput = bytearray()
    currentNode = tRoot
    for bit in encodedData:
        currentNode = currentNode.left if bit == '0' else currentNode.right
        if currentNode.char is not None:
            decodedOutput.append(currentNode.char)
            currentNode = tRoot
    return decodedOutput

def compressPdfFile(inputPdfPath):
    with open(inputPdfPath, "rb") as inputFile:
        fileData = inputFile.read()

    frequencyTable = defaultdict(int)
    for byte in fileData:
        frequencyTable[byte] += 1

    tree_root = buildHuffmanTree(frequencyTable)
    codeMap = generateHuffmanCodes(tree_root)
    encodedData = encodeInputData(fileData, codeMap)
    extraPadding = 8 - len(encodedData) % 8
    encodedData = f"{'0' * extraPadding}{encodedData}"

    byteArray = bytearray()
    for i in range(0, len(encodedData), 8):
        byteArray.append(int(encodedData[i:i + 8], 2))

    compressedOutputPath = inputPdfPath.replace(".pdf", "") + ".huff"
    with open(compressedOutputPath, "wb") as compressedFile:
        compressedFile.write(bytes([extraPadding]))
        compressedFile.write(len(frequencyTable).to_bytes(2, byteorder="big"))
        for char, freq in frequencyTable.items():
            compressedFile.write(bytes([char]))
            compressedFile.write(freq.to_bytes(4, byteorder="big"))
        compressedFile.write(byteArray)

    return tree_root, compressedOutputPath

def decompressPdfFile(inputCompressedPath, outputPdfPath):
    with open(inputCompressedPath, "rb") as compressedFile:
        extraPadding = compressedFile.read(1)[0]
        freqTableSize = int.from_bytes(compressedFile.read(2), byteorder="big")

        frequencyTable = {}
        for _ in range(freqTableSize):
            char = compressedFile.read(1)[0]
            freq = int.from_bytes(compressedFile.read(4), byteorder="big")
            frequencyTable[char] = freq

        encodedData = ""
        byteArray = compressedFile.read()
        for byte in byteArray:
            encodedData += f"{bin(byte)[2:].zfill(8)}"

    encodedData = encodedData[extraPadding:]
    tree_root = buildHuffmanTree(frequencyTable)
    decodedData = decodeEncodedData(encodedData, tree_root)

    with open(outputPdfPath, "wb") as decompressedFile:
        decompressedFile.write(decodedData)

    return outputPdfPath

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
DECOMPRESSED_FOLDER = 'decompressed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
os.makedirs(DECOMPRESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if 'pdf_file_compress' in request.files:
            pdf_file = request.files['pdf_file_compress']
            if pdf_file.filename == '':
                return "No selected file for compression", 400

            if pdf_file and pdf_file.filename.endswith('.pdf'):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
                pdf_file.save(file_path)

                tree_root, compressed_file_path = compressPdfFile(file_path)
                compressed_output_path = os.path.join(COMPRESSED_FOLDER, os.path.basename(compressed_file_path))

                if os.path.exists(compressed_output_path):
                    os.remove(compressed_output_path)

                os.rename(compressed_file_path, compressed_output_path)
                return send_file(compressed_output_path, as_attachment=True, download_name="compressed_file.huff")

        elif 'pdf_file_decompress' in request.files:
            compressed_file = request.files['pdf_file_decompress']
            if compressed_file.filename == '':
                return "No selected file for decompression", 400

            if compressed_file and compressed_file.filename.endswith('.huff'):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_file.filename)
                compressed_file.save(file_path)

                decompressed_output_path = os.path.join(DECOMPRESSED_FOLDER,
                                                        compressed_file.filename.replace('.huff', '.pdf'))
                decompressPdfFile(file_path, decompressed_output_path)
                return send_file(decompressed_output_path, as_attachment=True, download_name="decompressed_file.pdf")

        return "Invalid file type. Please upload a PDF or compressed file.", 400

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
