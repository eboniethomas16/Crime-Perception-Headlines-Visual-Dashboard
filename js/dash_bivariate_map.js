// 3×3 color matrix (perception bins = rows, crime bins = columns)

// -----------------------------------------------------------------------------
// EXPORT STUB (so scrollama can call updateMap before data is ready)
// -----------------------------------------------------------------------------
export function drawChoroMap({
                                     container,
                                     topoJSON,
                                     data,
                                     setHoverBorough,
                                     onClick,
                                        selectedMetric,

                                 }) {
    let currentMetric = selectedMetric;
    let fullData = data;   // store filtered mapData for this metric


    console.log("BIVARIATE map js is running");
    const geo = topojson.feature(topoJSON, topoJSON.objects.boroughs);

    // ORIGINAL aspect ratio
    const BASE_W = 420*2;
    const BASE_H = 480 *2;
    const ASPECT = (BASE_W / BASE_H);

    const containerNode = document.querySelector(container);
    function computeSize() {
        const cw = containerNode.clientWidth;
        const ch = containerNode.clientHeight;

        // Height-driven sizing
        let width = cw;
        let height = width / ASPECT;

        // If width exceeds container, shrink width instead
        if (height > ch) {
            height = ch;
            width = height * ASPECT;
        }

        return { width, height };
    }

    // INITIAL SIZE
    const { width: initWidth, height: initHeight } = computeSize();

    const svg = d3.select("#choro-map-content")
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")



    const wrapper = svg.append("g").attr("class", "map-wrapper");
    const mapGroup = wrapper.append("g").attr("class", "map-group");


    // Step 1: Fit projection to container
    let projection = d3.geoMercator().scale(1).translate([0, 0]);
    let path = d3.geoPath(projection);

    // Compute raw bounds
    const [[x0, y0], [x1, y1]] = path.bounds(geo);

    // Compute scale to fit container
    let scale = Math.min(
        initWidth / (x1 - x0),
        initHeight / (y1 - y0)
    );

    // Update projection scale
    projection.scale(scale);

    // Recompute path with new scale
    path = d3.geoPath(projection);

    // Compute translation
    const translateX = -x0 * scale + (initWidth - (x1 - x0) * scale) / 2;
    const translateY = -y0 * scale + (initHeight - (y1 - y0) * scale) / 2;

    // Apply transform
    mapGroup.attr("transform", `
    translate(${translateX+100}, ${translateY + -60})
        `);

    // Build lookup table for mapData
    const dataByBorough = new Map(
        fullData.map(d => [d.borough, d])
    );
    // Draw map
    let boroughPaths = mapGroup.selectAll(".borough")
        .data(geo.features)
        .join("path")
        .attr("class", "borough")
        .attr("d", path)
        .attr("fill", d => {
            const row = dataByBorough.get(d.id);
            return row ? row.color : "#ccc";
        })
        .on("mousemove", (event, d) => {
            // Update global hover state
            setHoverBorough(d.id);
        })
        .on("mouseout", (event, d) => {
            setHoverBorough(null);
        })
        .on("click", (event, d) => {
            //Clicking ACTIVATES THE BOROUGH
            const boroughName = d.id;
            onClick(boroughName);
        });

    // create borough label manual offsets
    const manualOffsets = {
        "Kensington and Chelsea": [0, 10],
        "Islington": [-10, 0],
        "Hammersmith and Fulham": [20, -15],
        "Hackney": [0, -10],
        "Camden": [0, 10],
        "Westminster": [0, 10]
    };
    //  Create label layer
    const labelLayer = mapGroup.append("g").attr("class", "label-layer");
    // add borough labels
    labelLayer.selectAll(".borough-label")
        .data(geo.features)
        .join("text")
        .attr("class", "borough-label")
        .attr("x", d => path.centroid(d)[0] + (manualOffsets[d.id]?.[0] || 0))
        .attr("y", d => path.centroid(d)[1] + (manualOffsets[d.id]?.[1] || 0))
        .text(d => d.id === "City of London" ? "" : d.id)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "#000")
        .attr("stroke", "#000000")
        .attr("stroke-width", 0.2)
        .style("pointer-events", "none");


    // Updates Color map data when perception metric changes
    function updateMetric(newMetric) {
        currentMetric = newMetric;
    }
    // When borough is selected, active boroughs signal are
    // sent to the rest of the dashboard
    function updateActiveBoroughs(activeSet) {

        boroughPaths
            .classed("active-highlight", d => activeSet.has(d.id))
            .classed("dimmed", d => activeSet.size > 0 && !activeSet.has(d.id));

        boroughPaths
            .filter(d => activeSet.has(d.id))
            // .raise();

        boroughPaths
            .filter(d => activeSet.size > 0 && !activeSet.has(d.id))
            .lower();

        //  Apply dimming to labels too
        labelLayer.selectAll(".borough-label")
            .classed("active-highlight", d => activeSet.has(d.id))
            .classed("dimmed", d => activeSet.size > 0 && !activeSet.has(d.id));
    }
    // hover highlights the area any hovered borough
    function highlightArea(boroughName) {
        boroughPaths
            .classed("hover-highlight", d => d.id === boroughName)
            .filter(d => d.id === boroughName)
            // .raise();   // hover ALWAYS raised last

    }
    // clears the highlight when user stops hovering over borough
    function clearAreaHighlight() {
        boroughPaths.classed("hover-highlight", false);
    }
    // as user moves through chart dates, the map coloring updates
    function updateMapForQuarter(quarterDate) {
        if (!quarterDate) return;

        // Filter map data for selected metric + quarter
        const filtered = fullData.filter(d =>
            d.metric === currentMetric &&
            +d.date === +quarterDate
        );

        const lookup = new Map(filtered.map(d => [d.borough, d.color]));

        boroughPaths
            .transition()
            .duration(250)
            .attr("fill", d => lookup.get(d.id) || "#ccc");
    }
    // Return API objects to the dashboard
    return {
        updateActiveBoroughs,
        highlightArea,
        clearAreaHighlight,
        updateMapForQuarter,
        updateMetric
    }
}

