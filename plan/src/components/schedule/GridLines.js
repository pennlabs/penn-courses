import React from "react";

export default function GridLines(props) {
    const { numRow, numCol } = props;
    const lastRow = Math.floor(numRow / 2) * 2;
    const rowstyle = { gridColumnStart: 2, gridColumnEnd: numCol + 1, position: "relative" };
    const colstyle = { gridRowStart: 2, gridRowEnd: lastRow, position: "relative" };

    const lines = [];
    for (let i = 2; i < Math.floor(numRow / 2) * 2; i += 2) {
        lines.push(<span className="horizontalLine" style={{ gridRow: i, ...rowstyle }} />);
    }
    lines.push(<span className="horizontalLine-last" style={{ gridRow: lastRow - 1, ...rowstyle }} />);

    for (let i = 2; i <= numCol; i += 1) {
        lines.push(<span className="verticalLine" style={{ gridColumn: i, ...colstyle }} />);
    }
    lines.push(<span className="verticalLine-last" style={{ gridColumn: numCol, ...colstyle }} />);

    return lines;
}
