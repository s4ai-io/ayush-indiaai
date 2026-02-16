
const d = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
];
const p = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
];
const inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9];

function generateVerhoeff(num: string): string {
    let c = 0;
    const myArray = String(num).split("").map(Number).reverse();
    for (let i = 0; i < myArray.length; i++) {
        c = d[c][p[(i + 1) % 8][myArray[i]]];
    }
    return inv[c].toString();
}

/**
 * Generates a mock ABHA ID (14 digits) using Verhoeff algorithm for checksum.
 * Format: XX-XXXX-XXXX-XXXX
 */
export function generateAbhaId(): string {
    // Generate 13 random digits
    let id = "";
    for (let i = 0; i < 13; i++) {
        id += Math.floor(Math.random() * 10);
    }

    // Calculate 14th digit (checksum)
    const checkDigit = generateVerhoeff(id);
    const fullId = id + checkDigit;

    // Format result
    return `${fullId.slice(0, 2)}-${fullId.slice(2, 6)}-${fullId.slice(6, 10)}-${fullId.slice(10, 14)}`;
}
