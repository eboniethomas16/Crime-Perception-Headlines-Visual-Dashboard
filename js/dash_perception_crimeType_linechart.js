export function drawPerceptionChart({
                                                 container,
                                                 data,          // [{ date, avg }] aggregated perception
                                                 x,
                                                 y,
                                                 width,
                                                 height,
                                                 margin,
                                                 onZoom
                                             }) {

    const chartContainer = d3.select(container);

    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height);
    let selectedMetric = null;

    let innerWidth  = width  - margin.left - margin.right;
    let innerHeight = height - margin.top  - margin.bottom;

    const clipRect = svg.append("defs")
        .append("clipPath")
        .attr("id", "clip-perception")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

    const chartGroup = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    const plotGroup = chartGroup.append("g")
        .attr("clip-path", "url(#clip-perception)");

    const xAxis = chartGroup.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
    const xLabel = chartGroup.append("text")
        .attr("class", "axis-label axis-label-x")
        .attr("text-anchor", "middle")
        .attr("fill", "#222")
        .style("font-family", "Poppins, sans-serif")
        .style("font-size", "12px")
        .text("Date");

    const yAxis = chartGroup.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(y).tickFormat(d => d + "%"));

    const yLabel = chartGroup.append("text")
        .attr("class", "axis-label axis-label-y")
        .attr("text-anchor", "middle")
        .attr("fill", "#222")
        .style("font-family", "Poppins, sans-serif")
        .style("font-size", "12px")
        .text("% of Residents That Agree");

    const lineGen = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.avg));

    let perceptionLine = null;
    positionAxisLabels()

    // ============================================================
    // 1. INITIALIZE
    // ============================================================
    function initializePerceptionChart(initialMetric = null, initialData = []) {
        // set internal metric and data
        selectedMetric = initialMetric;
        // data = Array.isArray(initialData) ? initialData : [];

        // set initial x/y ranges
        x.range([0, innerWidth]);
        y.range([innerHeight, 0]);

        xAxis.call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
        yAxis.call(d3.axisLeft(y).tickFormat(d => `${d}%`));

        // draw line if not present
        if (!perceptionLine) {
            perceptionLine = plotGroup.append("path")
                .attr("class", "perception-line")
                .attr("stroke", "#2a5599")
                .attr("stroke-width", 3)
                .attr("fill", "none")
                .datum(data)
                .attr("d", lineGen);
        } else {
            perceptionLine.datum(data).attr("d", lineGen);
        }
        positionAxisLabels()
    }


    // ============================================================
    // 6. UPDATE DATA
    // ============================================================
    function updateData(newData) {
        // newData must be an aggregated array: [{date, avg, metric}, ...]
        data = Array.isArray(newData) ? newData : [];
        // update scales domain if you want to auto-fit y (optional)
        // const maxY = d3.max(data, d => d.avg) ?? 100;
        // y.domain([0, Math.max(100, maxY)]);
        redrawXAxis();
        redrawLines();
    }

    // ============================================================
    // 6. SET METRIC TO NEW METRIC
    // ============================================================
    function setMetric(metricName, aggregatedArrayForMetric = null) {
        // set internal metric name
        selectedMetric = metricName;
        // if caller provides the aggregated array for this metric, bind it
        if (Array.isArray(aggregatedArrayForMetric)) {
            updateData(aggregatedArrayForMetric);
        } else {
            // otherwise just redraw using whatever data is currently bound
            redrawXAxis();
            redrawLines();
        }
    }


    // ============================================================
    // 2. ZOOM
    // ============================================================
    const brush = d3.brushX()
        .extent([[0, 0], [innerWidth, innerHeight]])
        .on("end", zoomIn);

    chartGroup.append("g")
        .attr("class", "zoom")
        .call(brush);

    function zoomIn(event) {
        if (!event.sourceEvent) return;
        const selection = event.selection;
        if (!selection) return;

        const [x0, x1] = selection;
        const newDomain = [x.invert(x0), x.invert(x1)];

        onZoom(newDomain);

        chartGroup.select(".zoom").call(brush.move, null);
    }

    // ============================================================
    // 3. APPLY X DOMAIN
    // ============================================================
    function applyXDomain(domain) {
        x.domain(domain);
        redrawXAxis();
        redrawLines();
    }

    // ============================================================
    // 4. REDRAW X AXIS
    // ============================================================
    function redrawXAxis() {
        xAxis.call(
            d3.axisBottom(x)
                .tickFormat(d3.timeFormat("%b %Y"))
        );
    }
    function positionAxisLabels() {
        xLabel
            .attr("x", innerWidth / 2)
            .attr("y", innerHeight + (margin.bottom ? Math.max(28, margin.bottom) : 40))
            .attr("text-anchor", "middle");

        // Y label: translate to the left of the plot area and vertically center, then rotate
        const yTranslateX = -margin.left + 14; // tweak this to move label closer/further from ticks
        const yTranslateY = innerHeight / 2;

        yLabel
            .attr("transform", `translate(${yTranslateX}, ${yTranslateY}) rotate(-90)`)
            .attr("text-anchor", "middle")
            .style("dominant-baseline", "middle");
    }

    // ============================================================
    // 5. REDRAW LINES
    // ============================================================
    function redrawLines() {
        if (!perceptionLine) return;

        // If data is an array of objects with metric field, filter by selectedMetric
        const series = Array.isArray(data) ? data.filter(d => d.metric === selectedMetric) : [];

        // update the bound datum and redraw path
        perceptionLine
            .datum(series)
            .transition()
            .duration(300)
            .attr("d", lineGen);
    }


    // function updateData(newData) {
    //     data = newData;
    //     redrawXAxis();
    //     redrawLines();
    // }


    // function setMetric(metricName) {
    //     selectedMetric = metricName;
    //     // update axes if needed and redraw the single line for the new metric
    //     redrawXAxis();
    //     redrawLines();
    // }

    // ============================================================
    // RETURN API
    // ============================================================
    return {
        initializePerceptionChart,
        applyXDomain,
        redrawXAxis,
        redrawLines,
        updateData,
        setMetric,
        plotGroupNode: plotGroup.node()
    };
}
