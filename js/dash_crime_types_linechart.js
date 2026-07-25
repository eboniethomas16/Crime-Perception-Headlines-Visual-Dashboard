function drawCrimeChart({
                                   container,
                                   data,
                                   x,
                                   y,
                                   width,
                                   height,
                                   margin,
                                   color,
                                   onLineClick,
                                   onZoom,
                               }) {

    console.log("CRIME Linechart js is running");
    const chartContainer = d3.select(container);

    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);

    let innerWidth  = width  - margin.left - margin.right;
    let innerHeight = height - margin.top  - margin.bottom;

    const clipRect = svg.append("defs")
        .append("clipPath")
        .attr("id", "crime-clip")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", "url(#crime-clip)");

    // ⭐ FIX: use innerHeight, not height - margin.bottom
    const xAxis = chartGroup.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(
            d3.axisLeft(y)
                .ticks(6)
                .tickFormat(d3.format(","))
        );

    const lineGen = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.crime_count));

    let boroughLines;

    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", zoomIn);

    chartGroup.append("g")
        .attr("class", "zoom")
        .call(brush);


    function initializeCrimeChart() {

        const byBorough = d3.group(data, d => d.borough);
        const boroughs = Array.from(byBorough);

        color.domain(boroughs.map(d => d[0]));

        boroughLines = plotGroup.selectAll(".crime-line")
            .data(boroughs, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "crime-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("fill", "none")
                    .attr("d", d => lineGen(d[1]))
                    .on("click", (event, d) => {
                        onLineClick(d[0]);
                    }),

                update => update
                    .attr("stroke", d => color(d[0]))
                    .attr("d", d => lineGen(d[1])),

                exit => exit.remove()
            );
    }

    function updateActiveCrimeTypes(activeSet) {

        boroughLines
            .classed("active-highlight", d => activeSet.has(d[0]))
            .classed("dimmed", d => activeSet.size > 0 && !activeSet.has(d[0]))

        boroughLines
            .filter(d => activeSet.has(d[0]))
            .raise();

        boroughLines
            .filter(d => !activeSet.has(d[0]))
            .lower();
    }
    function highlightLine(boroughName) {
        boroughLines
            .classed("hover-highlight", d => d[0] === boroughName)
            .filter(d => d[0] === boroughName)
            .raise();
    }
    function clearHoverHighlight() {
        boroughLines.classed("hover-highlight", false);
    }

    // ZOOMIN DUPLICATED IN BOTH CRIME AND PERCEPTION CHARTS
    function zoomIn(event) {
        if (!event.sourceEvent) return;
        const selection = event.selection;
        if (!selection) return;

        const [x0, x1] = selection;
        const newDomain = [x.invert(x0), x.invert(x1)];

        onZoom(newDomain);   // dashboard callback

        // Remove grey brush box
        chartGroup.select(".zoom").call(brush.move, null);
    }
    function applyXDomain(domain) {
        x.domain(domain);
        redrawLines();
        redrawXAxis();
    }


    function redrawXAxis() {
        chartGroup.select(".x-axis")
            .call(d3.axisBottom(x)
                .tickFormat(d3.timeFormat("%b %Y")));
    }

    function redrawLines() {

        const byBorough = d3.group(data, d => d.borough);
        const boroughs = Array.from(byBorough);

        // color.domain(boroughs.map(d => d[0]));

        boroughLines = plotGroup.selectAll(".crime-line")
            .data(boroughs, d => d[0])
            .join(
                enter => enter.append("path")
                    .attr("class", "crime-line")
                    .attr("stroke", d => color(d[0]))
                    .attr("fill", "none")
                    .attr("d", d => lineGen(d[1]))
                    .on("click", (event, d) => {
                        onLineClick(d[0]);
                    }),

                update => update
                    .attr("stroke", d => color(d[0]))
                    .attr("d", d => lineGen(d[1])),

                exit => exit.remove()
            );
    }


    return {
        initializeCrimeChart,
        applyXDomain,
        redrawXAxis,
        redrawLines,
        plotGroupNode: plotGroup.node(),
        xScale: x,
        updateActiveBoroughs: updateActiveCrimeTypes,
        highlightLine,
        clearHoverHighlight
    };
}
