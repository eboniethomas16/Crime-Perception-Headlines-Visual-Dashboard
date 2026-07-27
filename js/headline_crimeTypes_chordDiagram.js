//This file only draws the diagram.
// It does not load CSVs or compute matrices.
//matrix data is build in chord_matrix_builder.js

export function drawChordDiagram(chord, chordWrapper) {

    const chordDiagram = d3.select(chord);
    const wrapper = d3.select(chordWrapper);

    d3.csv("../data/headline_daily_top3_multicrime.csv").then(raw => {

        // Parse rows
        raw.forEach(d => {
            d.Day = new Date(d.Day);
            d.crime_types = d.crime_types.trim();
        });

        // ---------------------------------------------------------
        // Build co-occurrence matrix: MOVE TO  chord_matrix_builder.js
        // ---------------------------------------------------------
        const crimeLists = raw.map(d =>
            d.crime_types.split(",").map(x => x.trim())
        );

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

        const names = [...new Set(
            Object.keys(pairCounts).flatMap(k => k.split("||"))
        )].sort();

        const indexMap = Object.fromEntries(names.map((c, i) => [c, i]));

        const n = names.length;


        const matrix = Array.from({ length: n }, () => Array(n).fill(0));
        Object.entries(pairCounts).forEach(([key, count]) => {
            const [a, b] = key.split("||");
            const i = indexMap[a];
            const j = indexMap[b];
            matrix[i][j] = count;
            matrix[j][i] = count;
        });
        // ---------------------------------------------------------
        // STOP HERE, copy everything above for chord_matrix_builder.js
        // ---------------------------------------------------------

        console.log("Matrix:", matrix);
        console.log("Names:", names);

        // ---------------------------------------------------------
        // D3 v3 chord diagram (your existing code)
        // ---------------------------------------------------------

        const width = 900;
        const height = 900;
        const margin = 260;
        const innerRadius = Math.min(width, height) / 2 - margin;
        const outerRadius = innerRadius + 30;

        const fill = d3.scaleOrdinal(d3.schemeTableau10);



        const chord = d3.chord()
            .padAngle(0.05)
            .sortSubgroups(d3.descending)(matrix);


        const svg = chordDiagram.append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(" + (width / 2) + "," + (height / 2) + ")");

        // Groups
        const group = svg.append("g").selectAll("g")
            .data(chord.groups)
            .enter().append("g")
            .attr("class", "group");

        const arc = d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius);

        const ribbon = d3.ribbon()
            .radius(innerRadius);



        group.append("path")
            .style("fill", d => fill(d.index))
            .style("stroke", "#000")
            .attr("d", arc);


        // Labels
        group.append("text")
            .each(function (d) { d.angle = (d.startAngle + d.endAngle) / 2; })
            .attr("dy", ".35em")
            .attr("transform", function (d) {
                return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
                    + "translate(" + (outerRadius + 10) + ")"
                    + (d.angle > Math.PI ? "rotate(180)" : "");
            })
            .style("text-anchor", d => d.angle > Math.PI ? "end" : "start")
            .text(d => names[d.index]);

        // Ribbons
        const ribbons = svg.append("g")
            .attr("class", "ribbons")
            .selectAll("path")
            .data(chord)              // D3 v7: chord is an array of chords
            .enter().append("path")
            .attr("class", "ribbon")
            .attr("d", ribbon)
            .style("fill", d => fill(d.target.index))
            .style("stroke", "#000");


        // Hover fade
        // RIBBON HOVER
        ribbons.on("mouseover", function (event, d) {

            // Fade all ribbons except the hovered one
            ribbons
                .transition().duration(250)
                .style("opacity", r =>
                (r.source.index === d.source.index && r.target.index === d.target.index) ? 1 : 0.1
            );

            // Highlight only the two connected groups
            group.selectAll("path")
                .transition().duration(250)
                .style("opacity", g =>
                g.index === d.source.index || g.index === d.target.index ? 1 : 0.2
            );

            group.selectAll("text")
                .transition().duration(250)
                .style("opacity", g =>
                g.index === d.source.index || g.index === d.target.index ? 1 : 0.2
            );
        });

        ribbons.on("mouseout", function () {
            ribbons
                .transition().duration(250)
                .style("opacity", 0.7);
            group.selectAll("path")
                .transition().duration(250)
                .style("opacity", 1);
            group.selectAll("text")
                .transition().duration(250)
                .style("opacity", 1);
        });


// GROUP HOVER
        group.on("mouseover", function (event, d) {

            // Fade ribbons not connected to this group
            ribbons
                .transition().duration(250)
                .style("opacity", r =>
                r.source.index === d.index || r.target.index === d.index ? 1 : 0.1
            );

            // Highlight only this group
            group.selectAll("path")
                .transition().duration(250)
                .style("opacity", g =>
                g.index === d.index ? 1 : 0.2
            );

            group.selectAll("text")
                .transition().duration(250)
                .style("opacity", g =>
                g.index === d.index ? 1 : 0.2
            );
        });

        group.on("mouseout", function () {
            ribbons
                .transition().duration(250)
                .style("opacity", 0.7);
            group.selectAll("path").style("opacity", 1);
            group.selectAll("text").style("opacity", 1);
        });


    });
}
