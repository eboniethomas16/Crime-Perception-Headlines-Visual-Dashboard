//This file contains zero D3 code, only data logic.
//This file has no DOM, no SVG, no D3 layout.
// It only computes data for the crimeType_coocurrence chord diagram

export function buildCooccurrenceMatrix(rows) {

    // SAFETY CHECK
    if (!rows || !Array.isArray(rows)) {
        // console.error("build CooccurrenceMatrix: rows is not an array", rows);
        return { names: [], matrix: [] };
    }

    // If no rows → no matrix
    if (rows.length === 0) {
        return { names: [], matrix: [] };
    }

    // Extract crime type lists
    const crimeLists = rows
        .filter(d => d.crime_types && d.crime_types.trim() !== "")
        .map(d => d.crime_types.split(",").map(x => x.trim()));

    // If no crime types found
    if (crimeLists.length === 0) {
        return { names: [], matrix: [] };
    }

    // Count co-occurrences
    const pairCounts = {};

    crimeLists.forEach(list => {
        const unique = [...new Set(list)].sort();
        for (let i = 0; i < unique.length; i++) {
            for (let j = i + 1; j < unique.length; j++) {
                const key = `${unique[i]}||${unique[j]}`;
                pairCounts[key] = (pairCounts[key] || 0) + 1;
            }
        }
    });

    // Build names list
    const names = [...new Set(
        crimeLists.flatMap(list => list)
    )].sort();

    // If only one crime type → return 1×1 matrix
    if (names.length === 1) {
        return {
            names,
            matrix: [[0]]
        };
    }

    // Build empty square matrix
    const n = names.length;
    const indexMap = Object.fromEntries(names.map((c, i) => [c, i]));
    const matrix = Array.from({ length: n }, () => Array(n).fill(0));

    // Fill matrix with pair counts
    Object.entries(pairCounts).forEach(([key, count]) => {
        const [a, b] = key.split("||");
        const i = indexMap[a];
        const j = indexMap[b];
        matrix[i][j] = count;
        matrix[j][i] = count;
    });

    return { names, matrix };
}

