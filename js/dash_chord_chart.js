// dash_chord_chart.js
// A standalone D3 chord diagram module for headline crime-type co-occurrence

import { buildCooccurrenceMatrix } from "./chord_matrix_builder.js";

export function drawChordChart({
                                   container,
                                   data,          // raw headline rows
                                   width,
                                   height,
                                   margin = { top: 10, right: 40, bottom: 50, left: 40 },
                                   color
                               }) {

    //  Store raw headline rows inside the module
    let rawData = data;
    let crimeTypes = null;
    let matrixData = null;
    let groupSel = null;
    let ribbonsSel = null;

    //  Internal render function (used for initial draw + updates)
    // Utilizes chord_matrix_builder module
    function updateChordChart(filteredData) {

        // Remove old SVG
        d3.select(container).select("svg").remove();

        // -----------------------------
        // 1. Build co-occurrence matrix
        // -----------------------------
        const { names, matrix } = buildCooccurrenceMatrix(filteredData);
        crimeTypes = names;
        matrixData = matrix;

        // -----------------------------
        // 2. Dimensions
        // -----------------------------
        const outerWidth  = width;
        const outerHeight = height;

        const innerWidth  = outerWidth  - margin.left - margin.right;
        const innerHeight = outerHeight - margin.top  - margin.bottom;

        const radius = Math.min(innerWidth, innerHeight) / 2.5;

        // -----------------------------
        // 3. Color scale
        // -----------------------------
        // const color = colorScale || d3.scaleOrdinal()
        //     .domain(names)
        //     .range(d3.schemeTableau10);

        // -----------------------------
        // 4. Create SVG
        // -----------------------------
        const svg = d3.select(container)
            .append("svg")
            .attr("width", outerWidth)
            .attr("height", outerHeight)
            .append("g")
            .attr("transform", `translate(${margin.left + innerWidth/2}, ${margin.top + innerHeight/2})`);

        // -----------------------------
        // 5. Build chord layout
        // -----------------------------
        const chord = d3.chord()
            .padAngle(0.05)
            .sortSubgroups(d3.descending)
            (matrix);

        const arc = d3.arc()
            .innerRadius(radius - 40)
            .outerRadius(radius);

        const ribbon = d3.ribbon()
            .radius(radius - 40);

// build tooltip HTML for a group index

        // -----------------------------
        // 6. Draw groups (outer arcs)
        // -----------------------------
        const group = svg.append("g")
            .selectAll("g")
            .data(chord.groups, d => names[d.index])   // key by crime type name
            .join(
                enter => {
                    const g = enter.append("g").attr("class", "chord-group");
                    g.append("path")
                        .attr("fill", d => color(names[d.index]))
                        .attr("stroke", "#000")
                        .attr("stroke-width", 0.5)
                        .attr("d", arc)                // initial
                        .style("opacity", 0)
                        .transition()
                        .duration(700)
                        .style("opacity", 1);
                    return g;
                },
                update => {
                    update.select("path")
                        .transition()
                        .duration(700)
                        .attrTween("d", function(d) {
                            const interp = d3.interpolate(this._current || d, d);
                            this._current = interp(1);
                            return t => arc(interp(t));
                        });
                    return update;
                },
                exit => exit
                    .transition()
                    .duration(500)
                    .style("opacity", 0)
                    .remove()
            );

        groupSel = group;


        group.append("path")
            .attr("d", arc)
            .attr("fill", d => color(names[d.index]))
            .attr("stroke", "#000")
            .attr("stroke-width", 0.5);

        groupSel = group;


        // -----------------------------
        // 8. Draw ribbons (inner chords)
        // -----------------------------
        const ribbons = svg.append("g")
            .attr("class", "chord-ribbons")
            .selectAll("path")
            .data(chord, d => `${names[d.source.index]}-${names[d.target.index]}`)
            .join(
                enter => enter.append("path")
                    .attr("class", "chord-ribbon")
                    .attr("fill", d => color(names[d.target.index]))
                    .attr("stroke", "#000")
                    .attr("stroke-width", 0.3)
                    .style("opacity", 0)
                    .attr("d", ribbon)
                    .transition()
                    .duration(700)
                    .style("opacity", 0.8),

                update => update
                    .transition()
                    .duration(700)
                    .attrTween("d", function(d) {
                        const interp = d3.interpolate(this._current || d, d);
                        this._current = interp(1);
                        return t => ribbon(interp(t));
                    }),

                exit => exit
                    .transition()
                    .duration(500)
                    .style("opacity", 0)
                    .remove()
            );

        ribbonsSel = ribbons;


        ribbonsSel = ribbons;

        // -----------------------------
        // 8. CREATE TOOLTIPS
        // -----------------------------
        const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("display", "none")
            .style("position", "absolute")
            .style("pointer-events", "none")
            .style("z-index", 1000);


        // build tooltip HTML for a group index
        function buildGroupTooltipHtml(index) {
            const arcName = names[index];
            const row = matrix[index];
            const cooccurring = row
                .map((count, i) => ({ name: names[i], count, idx: i }))
                .filter(d => d.count > 0 && d.idx !== index)
                .sort((a, b) => b.count - a.count);

            let html = `<strong style="display:block;margin-bottom:6px">${arcName}</strong>`;
            if (cooccurring.length === 0) {
                html += `<div style="opacity:0.85">No co-occurrences</div>`;
            } else {
                html += cooccurring.map(c => `<div style="margin:2px 0"><span style="font-weight:600">${c.name}</span>: ${c.count}</div>`).join("");
            }
            return html;
        }

// safe tooltip positioning
        function positionTooltip(event) {
            const tooltipNode = tooltip.node();
            if (!tooltipNode) return;
            const padding = 12;
            const pageX = event.pageX !== undefined ? event.pageX : (event.clientX + window.scrollX);
            const pageY = event.pageY !== undefined ? event.pageY : (event.clientY + window.scrollY);
            const tooltipRect = tooltipNode.getBoundingClientRect();
            const winW = window.innerWidth;
            const winH = window.innerHeight;

            let left = pageX + 12;
            let top = pageY + 12;

            if (left + tooltipRect.width + padding > winW) left = pageX - tooltipRect.width - 12;
            if (top + tooltipRect.height + padding > winH) top = pageY - tooltipRect.height - 12;

            tooltip.style("left", `${left}px`).style("top", `${top}px`);
        }

        // LABELS: curved along the arc using textPath, reversed for bottom arcs, truncated to fit
        const labelArc = d3.arc()
            .innerRadius(radius - 18)   // label radius; tweak to move label closer/further
            .outerRadius(radius - 18);

        group.each(function(d) {
            // compute mid angle for flipping decision
            d.angle = (d.startAngle + d.endAngle) / 2;

            // build a path for the label; reverse direction for bottom arcs so text reads upright
            const pathD = (d.angle > Math.PI)
                ? labelArc({ startAngle: d.endAngle, endAngle: d.startAngle })
                : labelArc(d);

            // append an invisible path to use with textPath
            d3.select(this).append("path")
                .attr("id", `label-path-${d.index}`)
                .attr("d", pathD)
                .attr("fill", "none")
                .attr("stroke", "none");
        });

        function renderOutsideLabel(g, d, name, radius) {
            const midAngle = (d.startAngle + d.endAngle) / 2;
            const angleRad = midAngle - Math.PI / 2;

            const tickInner = radius - 6;
            const tickOuter = radius + 6;
            const labelDistance = 24;

            const x1 = Math.cos(angleRad) * tickInner;
            const y1 = Math.sin(angleRad) * tickInner;
            const x2 = Math.cos(angleRad) * tickOuter;
            const y2 = Math.sin(angleRad) * tickOuter;
            const lx = Math.cos(angleRad) * (tickOuter + labelDistance);
            const ly = Math.sin(angleRad) * (tickOuter + labelDistance);

            g.append("line")
                .attr("class", "label-tick")
                .attr("x1", x1).attr("y1", y1)
                .attr("x2", x2).attr("y2", y2)
                .attr("stroke", "#666")
                .attr("stroke-width", 1);

            g.append("path")
                .attr("class", "label-connector")
                .attr("d", `M ${x2} ${y2} L ${lx} ${ly}`)
                .attr("stroke", "#bbb")
                .attr("stroke-width", 1)
                .attr("fill", "none");

            const deg = (midAngle * 180 / Math.PI);
            const anchor = (deg > 90 && deg < 270) ? "end" : "start";
            const labelOffset = (anchor === "end") ? -6 : 6;

            g.append("text")
                .attr("class", "outside-label")
                .attr("x", lx + labelOffset)
                .attr("y", ly + 4)
                .style("text-anchor", anchor)
                .style("font-size", "12px")
                .style("fill", "#333")
                .text(name)
                .attr("title", name);
        }



        // truncate text to fit path length
        function truncateToFit(textNode, pathNode) {
            if (!textNode || !pathNode) return true;
            const pathLen = pathNode.getTotalLength();
            const txt = textNode.text();
            if (!txt) return true;
            // Return whether the rendered text length fits the path length
            return textNode.node().getComputedTextLength() <= pathLen;
        }


// remove any previous label nodes if re-rendering
        group.selectAll(".arc-label").remove();
        group.selectAll(".outside-label").remove();
        group.selectAll(".label-tick").remove();
        group.selectAll(".label-connector").remove();

        group.append("g")
            .attr("class", "arc-label")
            .each(function(d) {
                const g = d3.select(this);
                const name = names[d.index];
                const pathNode = document.getElementById(`label-path-${d.index}`);

                // If no path (shouldn't happen) fallback to outside label
                if (!pathNode) {
                    renderOutsideLabel(g, d, name, radius);
                    return;
                }

                // Append curved textPath
                const textEl = g.append("text")
                    .append("textPath")
                    .attr("xlink:href", `#label-path-${d.index}`)
                    .attr("startOffset", "30%")
                    .style("text-anchor", "middle")
                    .style("font-size", "12px")
                    .style("fill", "#333")
                    .text(name);

                // If it doesn't fit after trimming, remove curved text and render outside label
                const fits = truncateToFit(textEl, pathNode);
                if (!fits) {
                    // remove the curved text element we just added
                    g.selectAll("text").remove();
                    // render outside label with tick/connector
                    renderOutsideLabel(g, d, name, radius);
                }
            });


// SINGLE set of handlers for groups and ribbons (placed after ribbons exists)
        group.on("mouseover", function(event, d) {
            const index = d.index;
            // highlight ribbons and groups
            ribbons.style("opacity", r => (r.source.index === index || r.target.index === index) ? 1 : 0.1);
            group.selectAll("path").style("opacity", g => g.index === index ? 1 : 0.2);
            group.selectAll("text").style("opacity", g => g.index === index ? 1 : 0.2);

            // show tooltip
            tooltip.html(buildGroupTooltipHtml(index)).style("display", "block");
            positionTooltip(event);
        });

        group.on("mousemove", function(event) {
            positionTooltip(event);
        });

        group.on("mouseout", function() {
            ribbons.style("opacity", 0.8);
            group.selectAll("path").style("opacity", 1);
            group.selectAll("text").style("opacity", 1);
            tooltip.style("display", "none");
        });

        ribbons.on("mouseover", function(event, d) {
            ribbons.style("opacity", r =>
                (r.source.index === d.source.index && r.target.index === d.target.index) ? 1 : 0.1
            );
            group.selectAll("path").style("opacity", g =>
                g.index === d.source.index || g.index === d.target.index ? 1 : 0.2
            );
            group.selectAll("text").style("opacity", g =>
                g.index === d.source.index || g.index === d.target.index ? 1 : 0.2
            );

            // show tooltip for the source arc (or build combined tooltip if you prefer)
            tooltip.html(buildGroupTooltipHtml(d.source.index)).style("display", "block");
            positionTooltip(event);
        });

        ribbons.on("mousemove", function(event) {
            positionTooltip(event);
        });

        ribbons.on("mouseout", function() {
            ribbons.style("opacity", 0.8);
            group.selectAll("path").style("opacity", 1);
            group.selectAll("text").style("opacity", 1);
            tooltip.style("display", "none");
        });


    }
    // Highlight a group and its ribbons by crime type name
    function highlightGroup(crimeType) {
        if (!crimeTypes || !groupSel || !ribbonsSel) return;
        const idx = crimeTypes.indexOf(crimeType);
        if (idx === -1) {
            clearHighlight();
            return;
        }

        // dim all ribbons except those connected to idx
        ribbonsSel.style("opacity", r =>
            (r.source.index === idx || r.target.index === idx) ? 1 : 0.08
        );

        // dim groups and emphasize the hovered group
        groupSel.selectAll("path").style("opacity", g =>
            g.index === idx ? 1 : 0.2
        );
        groupSel.selectAll("text").style("opacity", g =>
            g.index === idx ? 1 : 0.2
        );
    }
    // Clear chord highlights
    function clearHighlight() {
        if (!groupSel || !ribbonsSel) return;
        ribbonsSel.style("opacity", 0.8);
        groupSel.selectAll("path").style("opacity", 1);
        groupSel.selectAll("text").style("opacity", 1);
    }
    // update diagram so active crime types visuals are seen
    function updateActiveCrimeTypes(activeSet) {

        // If no crime types selected → clear chart
        if (!activeSet || activeSet.size === 0) {
            clear();
            return;
        }

        // Filter rawData inside module
        const filtered = rawData.map(d => {
            const types = d.crime_types.split(",").map(t => t.trim());

            // Keep only the crime types the user selected
            const selectedTypes = types.filter(t => activeSet.has(t));

            return {
                ...d,
                crime_types: selectedTypes.join(",")
            };
        })
            // Keep only rows that have at least 1 selected crime type
            .filter(d => d.crime_types.length > 0);


        // Re-render chord chart
        updateChordChart(filtered);
    }
    // clear the visual rendering when
    // no crime categories are selected
    function clear() {
        // d3.select(container).select("svg").remove();
        // Keep or create the SVG once
        let svgRoot = d3.select(container).select("svg");
        if (svgRoot.empty()) {
            svgRoot = d3.select(container)
                .append("svg")
                .attr("width", width)
                .attr("height", height);
        }

// Clear only the inner <g>, not the whole SVG
        svgRoot.selectAll("*").remove();

        const svg = svgRoot.append("g")
            .attr("transform", `translate(${margin.left + innerWidth/2}, ${margin.top + innerHeight/2})`);

    }
    // 10. Return API
    return {
        updateChordChart,
        updateActiveCrimeTypes,
        clear,
        highlightGroup,
        clearHighlight
    };
}

