import heapq
from collections import defaultdict
import os


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


def compressFile(inputFilePath, compressedFolder):
    with open(inputFilePath, "rb") as inputFile:
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

    filename = os.path.basename(inputFilePath).split('.')[0]
    compressedOutputPath = os.path.join(compressedFolder, f"{filename}.huff")
    with open(compressedOutputPath, "wb") as compressedFile:
        compressedFile.write(bytes([extraPadding]))
        compressedFile.write(len(frequencyTable).to_bytes(2, byteorder="big"))

        for char, freq in frequencyTable.items():
            compressedFile.write(bytes([char]))
            compressedFile.write(freq.to_bytes(4, byteorder="big"))

        compressedFile.write(byteArray)

    return tree_root, compressedOutputPath


def decompressFile(inputCompressedPath, decompressedFolder):
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

    filename = os.path.basename(inputCompressedPath).split('.')[0]
    outputPdfPath = os.path.join(decompressedFolder, f"decompressed_{filename}.txt")
    with open(outputPdfPath, "wb") as decompressedFile:
        decompressedFile.write(decodedData)

    return outputPdfPath


uploadsFolder = "uploads"
compressedFolder = "compressed"
decompressedFolder = "decompressed"

inputFilePath = os.path.join(uploadsFolder, "sample.txt")

treeRoot, compressedPath = compressFile(inputFilePath, compressedFolder)
decompressedPath = decompressFile(compressedPath, decompressedFolder)

print(f"Compressed file: {compressedPath}")
print(f"Decompressed file: {decompressedPath}")
