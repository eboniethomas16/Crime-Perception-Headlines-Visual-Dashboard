// 3×3 color matrix (perception bins = rows, crime bins = columns)

// -----------------------------------------------------------------------------
// EXPORT STUB (so scrollama can call updateMap before data is ready)
// -----------------------------------------------------------------------------
export let updateMap = (metricOverride = null) => {
    console.warn("updateMap() called before map finished loading");
};
export let projection;
export let path;
export let geo;
let svg, legendSvg, tooltip, table, selectedQuarter, selectedMetric;
let quarterSelect, metricSelect;


function drawLegend(legendSvgWidth, legendSvgHeight) {
    legendSvg.selectAll("*").remove();

    const crimeBins = ["low", "med", "high"];
    const percBins  = ["low", "med", "high"];

    const palette = {
        "low-low":   "#e8e8e8",
        "med-low":   "#ace4e4",
        "high-low":  "#5ac8c8",
        "low-med":   "#dfb0d6",
        "med-med":   "#a5add3",
        "high-med":  "#5698b9",
        "low-high":  "#be64ac",
        "med-high":  "#8c62aa",
        "high-high": "#3b4994",
    };

    // ------------------------------------------------------------
    // 1. Define padding for labels
    // ------------------------------------------------------------
    const padTop    = legendSvgHeight * 0.10;
    const padBottom = legendSvgHeight * 0.18;   // extra for bottom label
    const padLeft   = legendSvgWidth  * 0.18;   // extra for rotated label
    const padRight  = legendSvgWidth  * 0.10;

    const innerWidth  = legendSvgWidth  - padLeft - padRight;
    const innerHeight = legendSvgHeight - padTop  - padBottom;

    // Grid must fit inside inner box
    const legendSize = Math.min(innerWidth, innerHeight);
    const cellSize   = legendSize / 3;
    const legendFont = cellSize * 0.32;

    // Top-left corner of the grid
    const gridX = padLeft + (innerWidth  - legendSize) / 2;
    const gridY = padTop  + (innerHeight - legendSize) / 2;

    const g = legendSvg.append("g")
        .attr("transform", `translate(${gridX}, ${gridY})`);

    // ------------------------------------------------------------
    // 2. Draw 3×3 grid
    // ------------------------------------------------------------
    for (let pi = 0; pi < 3; pi++) {
        for (let ci = 0; ci < 3; ci++) {
            const key = `${crimeBins[ci]}-${percBins[pi]}`;
            g.append("rect")
                .attr("x", ci * cellSize)
                .attr("y", (2 - pi) * cellSize)
                .attr("width", cellSize)
                .attr("height", cellSize)
                .attr("fill", palette[key])
                .attr("stroke", "#ccc");
        }
    }

    // ------------------------------------------------------------
    // 3. Bottom label (Crime axis)
    // ------------------------------------------------------------
    legendSvg.append("text")
        .attr("x", gridX + legendSize / 2)
        .attr("y", gridY + legendSize + legendFont * 0.9)
        .attr("text-anchor", "middle")
        .style("font-size", `${legendFont}px`)
        .text("Crime Count →");

    // ------------------------------------------------------------
    // 4. Left label (Perception axis)
    // ------------------------------------------------------------
    legendSvg.append("text")
        .attr("x", gridX - legendFont * 0.4)
        .attr("y", gridY + legendSize / 2)
        .attr("text-anchor", "middle")
        .attr("transform", `rotate(-90, ${gridX - legendFont * 0.4}, ${gridY + legendSize / 2})`)
        .style("font-size", `${legendFont}px`)
        .text("Perception % →");
}

export function sizeAndDraw() {
    // Read the ACTUAL rendered sizes of the SVGs (set by CSS)
    const mapBox = svg.node().getBoundingClientRect();
    const legendBox = legendSvg.node().getBoundingClientRect();

    const mapWidth = mapBox.width;
    const mapHeight = mapBox.height;

    const legendWidth = legendBox.width;
    const legendHeight = legendBox.height;

    svg
        .attr("width", mapWidth)
        .attr("height", mapHeight);

    legendSvg
        .attr("width", legendWidth)
        .attr("height", legendHeight);

    // Build projection using the true map size
    projection = d3.geoMercator().fitSize([mapWidth, mapHeight], geo);
    path       = d3.geoPath(projection);

    // Draw map with current projection
    updateMap();

    // Draw legend using its true size
    drawLegend(legendWidth, legendHeight);
}

// -----------------------------------------------------------------------------
// LOAD DATA
// -----------------------------------------------------------------------------
export const mapReady = Promise.all([
    d3.json("../data/london-boroughs.json"),   // TopoJSON
    d3.csv("../data/FULL_crime_perception_bins_colors.csv", d3.autoType)
]).then(([topo, t]) => {

    // -------------------------------------------------------------------------
    // SVG + TOOLTIP + PROJECTION
    // -------------------------------------------------------------------------

    // Assign to top-level variables (NO const!)
    geo = topojson.feature(topo, topo.objects.boroughs);
    table = t;

    svg = d3.select("#map");
    legendSvg = d3.select("#legend");
    tooltip = d3.select("#tooltip");

    // Helper to format dates as "Jan 2022", "Apr 2023", etc.
    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleString("en-GB", {
            month: "short",
            year: "numeric"
        });
    }

    // POPULATE DROPDOWN LISTS
    // Parse real dates from the "date" column
    const parsedDates = table.map(d => {
        const dateObj = new Date(d.date);
        return { raw: d.date, dateObj, label: formatDate(d.date) };
    }).filter(d => !isNaN(d.dateObj));  // remove invalid / 1970-01-01 artifacts

// Extract unique dates (in case duplicates exist)
    const uniqueDates = Array.from(
        new Map(parsedDates.map(d => [d.raw, d])).values()
    );

// Sort chronologically
    uniqueDates.sort((a, b) => a.dateObj - b.dateObj);

// This replaces your old "quarters" array
    const quarters = uniqueDates.map(d => d.label);

// And this maps label → raw date string
    const quarterToDate = new Map(
        uniqueDates.map(d => [d.label, d.raw])
    );

    const metrics = ["Good job", "Trust MPS", "Fair treatment"];

    //const quarterSelect = d3.select("#quarterSelect");
    const metricSelect  = d3.select("#metricSelect");

    // quarterSelect
    //     .selectAll("option")
    //     .data(quarters)
    //     .join("option")
    //     .attr("value", d => d)
    //     .text(d => d);

    metricSelect
        .selectAll("option")
        .data(metrics)
        .join("option")
        .attr("value", d => d)
        .text(d => d);

    // Default selections
    let selectedQuarter = quarters[0];
    let selectedMetric  = metrics[0];

    // -------------------------------------------------------------------------
// CREATE QUARTER SCROLLER
// -------------------------------------------------------------------------
    const scroller = d3.select("#quarterScroller");

// Build slider HTML inside the controls container
    scroller.html(`
    <input type="range" id="quarterRange" min="0" max="${quarters.length - 1}" value="0" step="1">
    <div class="ticks"></div>
    <div class="tick-labels"></div>
`);

    const rangeInput = document.getElementById("quarterRange");
    const ticksDiv = scroller.select(".ticks");
    const labelsDiv = scroller.select(".tick-labels");

    //MAKE SLIDE RANGE ONE LONGER THAN THE # OF DATES
    rangeInput.min = 0;
    rangeInput.max = quarters.length;   // 0 = null, 1..N = dates
    rangeInput.value = 0;               // start at null

    function positionTicks() {
        const thumbRadius = 9;
        // IMPORTANT: get the *actual* width of the slider element
        const sliderWidth = rangeInput.offsetWidth;
        const trackWidth = sliderWidth - thumbRadius *2 -36;
        const trackLeft = thumbRadius;

        const n = quarters.length;

        ticksDiv
            .style("left", `${trackLeft}px`)
            .style("width", `${trackWidth}px`);

        labelsDiv
            .style("left", `${trackLeft}px`)
            .style("width", `${trackWidth}px`);
        // Populate tick marks
        ticksDiv.selectAll("div.tick")
            .data(quarters)
            .join("div")
            .attr("class", "tick")
            .style("position", "absolute")
            .style("transform", "translateX(-50%)")
            .style("left", (d, i) => `${(i / (n - 1)) * trackWidth}px`);

        // Populate tick labels
        labelsDiv.selectAll("div.tick-label")
            .data(quarters)
            .join("div")
            .attr("class", "tick-label")
            .style("position", "absolute")
            .style("left", (d, i) => `${(i / (quarters.length - 1)) * 100}%`)
            .style("transform", "translateX(-50%)")
            .text(d => d);
    }

    positionTicks();
    window.addEventListener("resize", positionTicks);

// Default slider position
    rangeInput.value = quarters.indexOf(selectedQuarter);

// Slider → update map
    rangeInput.addEventListener("input", function () {
        const index = +this.value;

        if (index === 0) {
            selectedQuarter = null;
        } else {
            selectedQuarter = quarters[index - 1];
        }
        updateMap();
        // Optional: keep thumb centered when dragging
        this.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    });

    // -------------------------------------------------------------------------
    // UPDATE MAP (data join + tooltip)
    // -------------------------------------------------------------------------
    updateMap = function(metricOverride = null) {
        if (metricOverride) selectedMetric = metricOverride;

        const filtered = table.filter(d =>
            d.metric === selectedMetric &&
            (selectedQuarter
                ? d.date === quarterToDate.get(selectedQuarter)
                : true)  // null = no date filter
        );


        const dataByBorough = new Map(
            filtered.map(d => [d.Borough, d])
        );

        geo.features.forEach(f => {
            const name = f.id;
            const row  = dataByBorough.get(name);

            if (row) {
                f.properties.crime_bin   = row.crime_bin.trim();
                f.properties.perc_bin    = row.perc_bin.trim();
                f.properties.crime_count = +row.crime_count;
                f.properties.perception_value  = +row.perception_value;
                f.properties.color       = row.color;
            } else {
                f.properties.crime_bin   = null;
                f.properties.perc_bin    = null;
                f.properties.crime_count = null;
                f.properties.perception_value  = null;
                f.properties.color       = "#c4addc";
            }
        });

        svg.selectAll("path")
            .data(geo.features)
            .join("path")
            .attr("class", "borough")
            .attr("d", path)
            .attr("fill", d => d.properties.color || "#000000")
            .on("mousemove", (event, d) => {

                const name  = d.id;
                const crime = d.properties.crime_count;
                const perception  = d.properties.perception_value;
                console.log("mousemove detected for perception: ", d.properties);
                tooltip
                    .style("opacity", 1)
                    .style("position", "fixed")
                    .style("left", (event.clientX + 10) + "px")
                    .style("top", (event.clientY + 10) + "px")
                    .html(`
                <div style="font-weight:700;text-align:center;">${name}</div>
                <div><strong>Crime:</strong> ${crime != null ? crime.toLocaleString() : "No data"}</div>
                <div><strong>Perception:</strong> ${perception != null ? (perception * 100).toFixed(1) + "%" : "No data"}</div>
            `);
            })
            .on("mouseleave", () => tooltip.style("opacity", 0));
    };

    // quarterSelect.on("change", function() {
    //     selectedQuarter = this.value;
    //     updateMap();
    // });

    metricSelect.on("change", function() {
        selectedMetric = this.value;
        updateMap();
    });


    // -------------------------------------------------------------------------
    // LEGEND (3×3 MATRIX)
    // -------------------------------------------------------------------------



    // -------------------------------------------------------------------------
    // HOOK UP DROPDOWNS
    // -------------------------------------------------------------------------


    // -------------------------------------------------------------------------
    // INITIAL DRAW (after layout)
    // -------------------------------------------------------------------------

    //requestAnimationFrame(sizeAndDraw);

});


// Convert TopoJSON → GeoJSON
//const geo = topojson.feature(topo, topo.objects.boroughs);
//window.__geo__ = geo;
// -------------------------------------------------------------------------
// DROPDOWNS
// -------------------------------------------------------------------------
// const quarterDates = new Map(
//     table.map(d => [d.Quarter, new Date(d.date)])
// );
//
// const quarters = [...new Set(table.map(d => d.Quarter))]
//     .sort((a, b) => quarterDates.get(a) - quarterDates.get(b));
//
// const metrics = ["Good job", "Trust MPS", "Fair treatment"];
//
// const quarterSelect = d3.select("#quarterSelect");
// const metricSelect  = d3.select("#metricSelect");



// let selectedQuarter = quarters[0];
// let selectedMetric  = metrics[0];


// // 3×3 color matrix (perception bins = rows, crime bins = columns)
// // -----------------------------------------------------------------------------
// // LOAD DATA
// // -----------------------------------------------------------------------------
// export let updateMap = (metricOverride = null) => {
//     console.warn("updateMap() called before map finished loading");
// };
//
// export const mapReady = Promise.all([
//     d3.json("london-boroughs.json"),   // TopoJSON
//     d3.csv("FULL_crime_perception_bins_colors.csv", d3.autoType)
// ]).then(([topo, table]) => {
//
//     // Convert TopoJSON → GeoJSON
//     const geo = topojson.feature(topo, topo.objects.boroughs);
//
//     // POPULATE DROPDOWN LISTS
//     // map Quarter to Date objects
//     const quarterDates = new Map(
//         table.map(d => [d.Quarter, new Date(d.date)])
//     );
//
//     // Extract unique values
//     const quarters = [...new Set(table.map(d => d.Quarter))]
//         .sort((a, b) => quarterDates.get(a) - quarterDates.get(b));
//
//     const metrics = ["Good job", "Trust MPS", "Fair treatment"];
//
//     const quarterSelect = d3.select("#quarterSelect");
//     const metricSelect  = d3.select("#metricSelect");
//
//     quarterSelect
//         .selectAll("option")
//         .data(quarters)
//         .join("option")
//         .attr("value", d => d)
//         .text(d => d);
//
//     metricSelect
//         .selectAll("option")
//         .data(metrics)
//         .join("option")
//         .attr("value", d => d)
//         .text(d => d);
//
//     // Default selections
//     let selectedQuarter = quarters[0];
//     let selectedMetric  = metrics[0];
//
//
//     // function updateMap() {
//     updateMap = function(metricOverride = null) {
//         if (metricOverride) selectedMetric = metricOverride;
//
//         // ---------------------------------------------------------------------------
//         // FILTER CSV rows based on user selection
//         // ---------------------------------------------------------------------------
//         const filtered = table.filter(d =>
//             d.metric === selectedMetric &&
//             d.Quarter === selectedQuarter
//         );
//
//         // (Optional: debug)
//         console.log("Filtered rows:", filtered.length);
//
//         // Build lookup table: Borough → row
//         const dataByBorough = new Map(
//             filtered.map(d => [d.Borough, d])
//         );
//
//         // ---------------------------------------------------------------------------
//         // JOIN CSV → GEOJSON
//         // ---------------------------------------------------------------------------
//         geo.features.forEach(f => {
//             const name = f.id;  // TopoJSON → GeoJSON: borough name is in `id`
//             const row = dataByBorough.get(name);
//
//             if (row) {
//                 f.properties.crime_bin = row.crime_bin.trim();
//                 f.properties.perc_bin = row.perc_bin.trim();
//                 f.properties.crime_count = +row.crime_count;
//                 f.properties.perc_value = +row.perc_value;
//                 f.properties.color = row.color;
//
//             } else {
//                 f.properties.crime_bin = null;
//                 f.properties.perc_bin = null;
//                 f.properties.crime_count = null;   // ← ADD THIS
//                 f.properties.perc_value = null;   // ← ADD THIS
//                 f.properties.color = "#f0f0f0";        // < ADD THIS
//             }
//         });
//
//
//         // ---------------------------------------------------------------------------
//         // PROJECTION + PATH
//         // ---------------------------------------------------------------------------
//         const svg = d3.select("#map");
//         const legendSvg = d3.select("#legend");
//         const tooltip = d3.select("#tooltip");
//
//         const figureNode = document.querySelector("#scrolly figure");
//         const figureWidth = figureNode.clientWidth;
//         const figureHeight = figureNode.clientHeight;
//
//         // Allocate space: map gets ~70%, legend gets ~30%
//         // const mapWidth = figureWidth;
//         // const mapHeight = figureHeight;
//         const wrapperBox = document.querySelector("#map-wrapper").getBoundingClientRect();
//         const mapWidth = wrapperBox.width;
//         const mapHeight = wrapperBox.height;
//
//         const projection = d3.geoMercator().fitSize([mapWidth, mapHeight], geo);
//         const path = d3.geoPath(projection);
//
//         // ---------------------------------------------------------------------------
//         // DRAW MAP
//         // ---------------------------------------------------------------------------
//         svg.selectAll("path")
//             .data(geo.features)
//             .join("path")
//             .attr("class", "borough")
//             .attr("d", path)
//             .attr("fill", d => d.properties.color || "#000000")
//             .on("mousemove", (event, d) => {
//                 const name = d.id;
//                 const crime = d.properties.crime_count;
//                 const perc = d.properties.perc_value;
//
//                 tooltip
//                     .style("opacity", 1)
//                     .style("left", (event.pageX + 10) + "px")
//                     .style("top", (event.pageY + 10) + "px")
//                     .html(`
//                 <div style="font-weight:700;text-align:center;">${name}</div>
//                 <div><strong>Crime:</strong> ${crime != null ? crime.toLocaleString() : "No data"}</div>
//                 <div><strong>Perception:</strong> ${perc != null ? (perc * 100).toFixed(1) + "%" : "No data"}</div>
//             `);
//             })
//             .on("mouseleave", () => tooltip.style("opacity", 0));
//     }
//
//     quarterSelect.on("change", function() {
//         selectedQuarter = this.value;
//         updateMap();
//     });
//
//     metricSelect.on("change", function() {
//         selectedMetric = this.value;
//         updateMap();
//     });
//
//     updateMap();
//
//     // ---------------------------------------------------------------------------
//     // LEGEND (3×3 MATRIX)
//     // ---------------------------------------------------------------------------
//
//     const crimeBins = ["low", "med", "high"];
//     const percBins  = ["low", "med", "high"];
//
//     const palette = {
//         "low-low":   "#e8e8e8",
//         "med-low":   "#ace4e4",
//         "high-low":  "#5ac8c8",
//         "low-med":   "#dfb0d6",
//         "med-med":   "#a5add3",
//         "high-med":  "#5698b9",
//         "low-high":  "#be64ac",
//         "med-high":  "#8c62aa",
//         "high-high": "#3b4994",
//     };
//
//     // Compute centered X position inside the legend SVG
//     const legendSvgWidth = figureWidth * 0.25;
//     const legendSvgHeight = figureHeight * 0.9;
//
//     // Apply sizes to SVGs
//     svg.attr("width", mapWidth).attr("height", mapHeight);
//     legendSvg.attr("width", legendSvgWidth).attr("height", legendSvgHeight);
//
//     const legendSize = Math.min(legendSvgWidth, legendSvgHeight);
//     const cellSize = legendSize / 3;
//     const legendFont = cellSize * 0.3;
//
//
//     // Center legend inside its SVG
//     const legendX = (legendSvgWidth - legendSize) / 2;
//     const legendY = (legendSvgHeight - legendSize) / 2;
//
//     const gLegend = legendSvg
//         .append("g")
//         .attr("transform", `translate(${legendX}, ${legendY-200})`);
//
// // Draw 3×3 grid: perc (rows), crime (cols)
//     for (let pi = 0; pi < percBins.length; pi++) {
//         for (let ci = 0; ci < crimeBins.length; ci++) {
//             const key = `${crimeBins[ci]}-${percBins[pi]}`;
//             const color = palette[key];
//
//             gLegend.append("rect")
//                 .attr("x", ci * cellSize)           // crime: low → med → high (left → right)
//                 .attr("y", (2 - pi) * cellSize)     // perc: low at bottom, high at top
//                 .attr("width", cellSize)
//                 .attr("height", cellSize)
//                 .attr("fill", color)
//                 .attr("stroke", "#ccc");
//         }
//     }
//
// // Bottom label
//     gLegend.append("text")
//         .attr("x", legendSize / 2)
//         .attr("y", legendSize + legendFont * 1.4)
//         .attr("text-anchor", "middle")
//         .style("font-size", `${legendFont}px`)
//         .text("Crime Count →");
//
// // Left label
//     gLegend.append("text")
//         .attr("x", -legendSize / 2)
//         .attr("y", -legendFont * 0.4)
//         .attr("text-anchor", "middle")
//         .attr("transform", "rotate(-90)")
//         .style("font-size", `${legendFont}px`)
//         .text("Perception % →");
// });



