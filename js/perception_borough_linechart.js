// Chart module
// → reusable function that draws the chart anywhere
// js/crime_borough_linechart.js

export function drawPerceptionBoroughChart(chart_PerceptionBorough, legend_PerceptionBorough, list_hoverListContainer) {

    // POSITION THE CHART + LEGEND SIDE BY SIDE
    // Position chart + legend side-by-side
    const chartContainer = d3.select(chart_PerceptionBorough);
    const legendContainer = d3.select(legend_PerceptionBorough);
    const tooltip = d3.select("#tooltip");
    const hoverListContainer = d3.select(list_hoverListContainer);


    let activeBoroughs = new Set(); //list of borough selected in legend
    let selectedHoverRow = null;   // stores borough name when clicked in hoverlist
    //this controls which boroughline is highlighted

    // Apply layout styles directly
    chartContainer
        .style("display", "inline-block")
        .style("vertical-align", "top");


    //positions it to the right of legend
    hoverListContainer
        .attr("class", "hover-list")
        // .style("opacity",0)
        // .transition().duration(0);


    // Load data
    d3.csv("../data/MOPAC_FULL_LONG_Public_Perception.csv").then(data => {

        // Parse date
        const parseOriginal = d3.timeParse("%m/%d/%Y");   // matches your raw data
        const formatMonthYear = d3.timeFormat("%b-%Y");   // "Jan-2015"
        const parseMonthYear = d3.timeParse("%b-%Y");     // final Date object

        data.forEach(d => {
            const raw = parseOriginal(d.date);  // parse "1/1/2015"
            if (!raw) {
                // console.warn("Bad date:", d.date);
                return;
            }

            const monthYearString = formatMonthYear(raw);  // "Jan-2015"
            d.date = parseMonthYear(monthYearString);      // Date object for Jan 2015

            d.metric_value = +d.metric_value;
            d.metric_value_pct = Math.round(d.metric_value * 100);   // stays numeric

            //Convert to percentage

        });
        // ---------- FILTER TO >= APRIL 2017 ----------
        //const cutoff = new Date(2014, 3, 1);   // month index 3 = April
        data = data.filter(d => d.date);

        // Group by borough
        const boroughs = d3.groups(data, d => d.borough);

        // Get the most recent date on screen
        const latestDate = d3.max(data, d => d.date);

        // ---------- CHART DIMENSIONS ----------
        const margin = { top: 10, right: 40, bottom: 40, left: 60 };
        const width = 700 - margin.left - margin.right;
        const height = 450 - margin.top - margin.bottom;


        // Create SVG
        const chartSVG = chartContainer
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        // lines within the chart container (lines, axes, axes labels)
        const chartGroup = chartSVG
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // CLIPS THE SVG WHEN BRUSHING SO BOROUGH LINES
        // DONT APPEAR OUTSIDE THE CHART
        chartSVG.append("defs")
            .append("clipPath")
            .attr("id", "clip")
            .append("rect")
            .attr("width", width)
            .attr("height", height -30);


        // NOW BUILD + STYLE THE LEGEND CONTAINER
        legendContainer
            .style("display", "inline-block")
            .style("vertical-align", "top")
            .style("margin-left", "5px")
            .style("width", "220px")
            .style("overflow-y", "auto")
            .style("height", (height - margin.top) + "px")
            .style("border", "1px solid #ddd")
            .style("padding", "10px")
            .style("background", "#fafafa");


        const hoverLine = chartGroup.append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", height)
            // .style("opacity", 0);

        // ---------- SCALES ----------
        // X scale
        const fullXDomain = d3.extent(data, d => d.date);

        const x = d3.scaleTime()
            .domain(fullXDomain)
            .range([0, width]);

        chartGroup.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
            .call(d3.axisBottom(x));


        // Y scale
        const y = d3.scaleLinear()
            .domain([0, 100])
            .range([height, 0]);

        chartGroup.append("g")
            .attr("class", "y-axis");


        // Color scale
        const color = d3.scaleOrdinal()
            // .domain(boroughs.map(d => d[0]))
            .range(d3.schemeTableau10);

        // legendContainer.style

        // ---------- DRAW LINES ----------
        const lineGen = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.metric_value_pct));


        // Draw lines
        let boroughLines;

        updatePerceptionChart();

        // updateHoverList(null, [], false);

        // listener for Redraw when dropdown changes
        d3.select("#perception-metric-select").on("change", updatePerceptionChart);

        // ---------- ZOOM OBJECT ----------
        const zoom = d3.brushX()
            .extent([[0, 0], [width, height]])
            .on("end", zoomIn);

        const brushGroup = chartGroup.append("g")
            .attr("class", "zoom")
            .call(zoom);
        brushGroup.raise();

        // ---------- LEGEND HIGHLIGHT INTERACTION ----------

        function updatePerceptionChart() {
            console.log("Dropdown changed");


            const selectedMetric = d3.select("#perception-metric-select").property("value");

            // 1️⃣ Filter dataset to only the chosen metric
            const filtered = data.filter(d => d.metric === selectedMetric);


            // 2️⃣ Group by borough
            const byBorough = d3.group(filtered, d => d.borough);

            // 3️⃣ Convert to array for binding
            const boroughs = Array.from(byBorough);

            // Update color domain
            color.domain(boroughs.map(d => d[0]));

            // 4️⃣ Update scales
            x.domain(d3.extent(filtered, d => d.date));

            // Perception values are percentages → fix y domain
            y.domain([0, 100]).nice();

            // Update axes
            chartGroup.select(".x-axis")
                .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

            chartGroup.select(".y-axis")
                .call(
                    d3.axisLeft(y)
                        .tickFormat(d => d + "%")   // ✔ show percentages
                );

            // 6️⃣ Bind data to lines using JOIN (important!)
            boroughLines = chartGroup.selectAll(".lines")
                .data(boroughs, d => d[0])
                .join(
                    enter => enter.append("path")
                        .attr("class", "lines")
                        .attr("clip-path", "url(#clip)")
                        .attr("stroke", d => color(d[0]))
                        .attr("fill", "none")
                        .attr("d", d => lineGen(d[1])),
                    update => update
                        .attr("stroke", d => color(d[0]))
                        .attr("d", d => lineGen(d[1])),
                    exit => exit.remove()
                );
            // ⭐ RE-ATTACH MOUSE EVENTS TO NEW LINE ELEMENTS
            boroughLines.on("mousemove", function(event, d) {
                //
                // if (!activeBoroughs.has(d[0])) {
                //     hideTooltip();
                //     return;
                // }
                //
                // const selectedMetric = d3.select("#perception-metric-select").property("value");
                //
                // // Use chartGroup as reference (NOT the path element)
                // const [mx] = d3.pointer(event, chartGroup.node());
                // const rawDate = x.invert(mx);
                //
                // // Snap to nearest date for THIS borough
                // const closest = d[1].reduce((a, c) =>
                //     Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
                // );
                //
                // const dataPoint = closest;
                //
                // showTooltip(event, {
                //     borough: d[0],
                //     metric_value: dataPoint.metric_value,
                //     metric_value_pct: dataPoint.metric_value_pct,
                //     date: dataPoint.date,
                //     selectedMetric: selectedMetric
                // });
                //
                // updateHoverList(dataPoint.date, [{
                //     borough: d[0],
                //     metric_value: dataPoint.metric_value,
                //     metric_value_pct: dataPoint.metric_value_pct
                // }], true);
            });



            // ⭐ If NO boroughs are active → clear hoverlist
            if (activeBoroughs.size === 0) {
                updateHoverList(null, [], false);
                console.log("Hoverlist CLEARED");
            } else {
                // ⭐ If boroughs ARE active → update hoverlist to reflect new metric
                showLatestValues(true);
                console.log("Hoverlist CHANGED TO NEW METRIC DATA");
            }

            // const maxVal = d3.max(filtered, d => d.metric_value_pct);


        }


        function highlightBoroughs(selected) {
            activeBoroughs.add(selected);

            boroughLines.classed("transition-tick", false);

            requestAnimationFrame(() => {
                boroughLines.classed("transition-tick", true)
                    .classed("highlighted", l => activeBoroughs.has(l[0]))
                    .classed("dimmed", l => !activeBoroughs.has(l[0]));
            });

            // Bring selected lines to front
            boroughLines.filter(l => activeBoroughs.has(l[0])).raise();
            // Lower inactive boroughs
            boroughLines.filter(l => !activeBoroughs.has(l[0])).lower();

            // Legend dimming
            legendItems.style("opacity", l => activeBoroughs.has(l[0]) ? 1 : 0.4);


            // When a borough is selected, show latest date in hoverlist
            showLatestValues(true);
        }


        function unhighlightBoroughs(selected) {
            activeBoroughs.delete(selected);

            // If nothing selected → full reset
            if (activeBoroughs.size === 0) {
                resetHighlights();
                return;
            }

            boroughLines.classed("transition-tick", false);

            requestAnimationFrame(() => {
                boroughLines.classed("transition-tick", true)
                    .classed("highlighted", l => activeBoroughs.has(l[0]))
                    .classed("dimmed", l => !activeBoroughs.has(l[0]));
            });

            // Raise active boroughs
            boroughLines.filter(l => activeBoroughs.has(l[0])).raise();

            // Lower inactive boroughs (including previously highlighted ones)
            boroughLines.filter(l => !activeBoroughs.has(l[0])).lower();

            // Dim legend items
            legendItems.style("opacity", l => activeBoroughs.has(l[0]) ? 1 : 0.4);

            updateHoverList(null, [], false);
        }

        function resetHighlights() {
            activeBoroughs.clear();

            boroughLines
                .classed("highlighted", false)
                .classed("dimmed",false);
                // .transition().duration(300)
                // .attr("opacity", 0.9)
                // .attr("stroke-width", 2);

            legendItems.style("opacity", 1);

            // Clear hover list completely
            updateHoverList(null, [], false);
        }

        // function showTooltip(event, d) {
        //     const selectedMetric = d3.select("#perception-metric-select").property("value");
        //
        //     tooltip.style("opacity", 1).html(`
        //         <div style="
        //             font-weight:700;
        //             text-align:center;
        //
        //         ">
        //             ${d3.timeFormat("%b %Y")(d.date)}
        //         </div>
        //
        //         <div style="
        //             font-weight:600;
        //             text-align:center;
        //             margin-bottom:4px;
        //         ">
        //             Metric: <strong>${selectedMetric}</strong>
        //         </div>
        //
        //         <div style="
        //             font-weight:700;
        //             text-align:center;
        //             font-size:22px;
        //             margin-top:4px;
        //         ">
        //             ${d.metric_value_pct}%
        //         </div>
        //     `)
        //         .style("left", (event.pageX + 12) + "px")
        //         .style("top", (event.pageY + 12) + "px");
        //
        // }
        //
        // function hideTooltip() {
        //     tooltip.style("opacity", 0);
        // }

        // ---------- HOVER LIST UPDATING ----------
        function updateHoverList(date, boroughDataArray, showDate = true) {
            // Clear previous content
            // Always re-read the selected metric
            const selectedMetric = d3.select("#perception-metric-select").property("value");

            // Filter data to the current metric
            const filtered = data.filter(d => d.metric === selectedMetric);

            // Group by borough for this metric
            const byBorough = d3.group(filtered, d => d.borough);
            const boroughsForMetric = Array.from(byBorough);


            // If no boroughs are active → hide hoverlist
            if (activeBoroughs.size === 0) {
                hoverListContainer
                    .style("opacity", 0)
                    .style("display", "none");
                return;
            }
            // if there ARE activeBoroughs then.....
            // Boroughs ARE active → hoverlist must be visible
            hoverListContainer
                .style("opacity", 1)
                .style("display", "inline-block");

            // Clear previous content
            hoverListContainer.selectAll("*").remove();

            // Month-year header
            if (showDate) {
                hoverListContainer
                    .append("div")
                    .style("font-weight", "600")
                    .style("margin-bottom", "8px")
                    .text(d3.timeFormat("%b %Y")(date));
            }

            // For each highlighted borough, add a row
            const hoverListRows = hoverListContainer
                .selectAll(".hover-row")
                .data(boroughDataArray, d => d.borough)
                .join(
                    enter => enter.append("div")
                        .attr("class", "hover-row")
                        .style("display", "flex")
                        .style("align-items", "center")
                        .style("margin", "4px 0")
                        .call(addHoverRowListeners),
                    update => update.call(addHoverRowListeners),
                    exit => exit.remove()
                );


            // Colored circle
            hoverListRows.append("div")
                .style("width", "12px")
                .style("height", "12px")
                .style("border-radius", "50%")
                .style("margin-right", "8px")
                .style("background-color", d => color(d.borough));

            // () Borough name: perception%
            hoverListRows.append("span")
                .html(d => `${d.borough}: <strong>${d.metric_value_pct}%</strong>`);

        }

        function addHoverRowListeners(selection) {
            selection
                .on("mouseover", (event, d) => {
                    const boroughName = d.borough;
                    boroughLines
                        .filter(l => l[0] === boroughName)
                        .raise()
                        .classed("hover-highlight", true);
                })
                .on("mouseout", (event, d) => {
                    const boroughName = d.borough;

                    // Only remove hover highlight if this row is NOT the selected one
                    if (selectedHoverRow !== boroughName) {
                        boroughLines
                            .filter(l => l[0] === boroughName)
                            .classed("hover-highlight", false);
                    }
                })
                .on("click", (event, d) => {
                    const boroughName = d.borough;

                    // Clear previous selection
                    if (selectedHoverRow) {
                        hoverListContainer
                            .selectAll(".hover-row")
                            .classed("selected-hover-row", r => r.borough === selectedHoverRow ? false : null);

                        boroughLines
                            .filter(l => l[0] === selectedHoverRow)
                            .classed("hover-highlight", false);
                    }

                    // Set new selection
                    selectedHoverRow = boroughName;

                    // Apply persistent highlight to current row
                    d3.select(event.currentTarget)
                        .classed("selected-hover-row", true);

                    // Persistent highlight on the line
                    boroughLines
                        .filter(l => l[0] === boroughName)
                        .raise()
                        .classed("hover-highlight", true);
                });
        }


        // build the list for the latest date
        function showLatestValues(showDate = true) {

            // ⭐ Always re-read the selected metric
            const selectedMetric = d3.select("#perception-metric-select").property("value");

            // ⭐ Filter data to the current metric
            const filtered = data.filter(d => d.metric === selectedMetric);

            // ⭐ Group by borough
            const byBorough = d3.group(filtered, d => d.borough);

            // ⭐ Convert to array
            const boroughsForMetric = Array.from(byBorough);
            // console.log("Selected Borough:" boroughsforMetric);
            // ⭐ Compute latest date for THIS metric
            const latestDateForMetric = d3.max(filtered, d => d.date);

            // ⭐ Build array of highlighted boroughs at the latest date
            const latestData = boroughsForMetric
                .filter(b => activeBoroughs.has(b[0]))
                .map(b => {
                    const last = b[1].find(r => r.date.getTime() === latestDateForMetric.getTime());
                    return {
                        borough: b[0],
                        metric_value: last.metric_value,
                        metric_value_pct: last.metric_value_pct,
                        date: last.date
                    };
                });

            // ⭐ Update hoverlist
            updateHoverList(latestDateForMetric, latestData, showDate);
        }


        // function showLatestValues(showDate = true) {
        //     // Build array of highlighted boroughs at the latest date
        //     const latestData = boroughs
        //         .filter(b => activeBoroughs.has(b[0]))
        //         .map(b => {
        //             const last = b[1][b[1].length - 1];   // last row for this borough
        //             return {
        //                 borough: b[0],
        //                 metric_value: last.metric_value,
        //                 metric_value_pct: last.metric_value_pct, // for the percentage
        //                 date: last.date
        //             };
        //         });
        //
        //     updateHoverList(latestDate, latestData, showDate);
        // }

        let hasZoomed = false;
        function zoomIn(event) {
            if (!event.sourceEvent) return;
            const selection = event.selection;

            // If user cleared the brush → reset zoom
            if (!selection) {
                applyXDomain(fullXDomain);
                chartGroup.select(".x-axis")
                    .call(d3.axisBottom(x));
                return;
            }
            // Convert pixel range → date range
            const [x0, x1] = selection;
            const newDomain = [x.invert(x0), x.invert(x1)];

            //Show the Reset Button
            hasZoomed = true;
            document.getElementById("resetZoomBtn").style.display = "inline-block";

            // Update x-scale domain
            x.domain(newDomain);

            // Apply updated zoomed domain
            applyXDomain(newDomain);

        }

        //re-renders your borough lines using the updated x‑scale.
        function redrawLines() {
            boroughLines
                .attr("d", d => lineGen(d[1]));   // lineGen uses updated x()
        }

        function redrawXAxis() {
            chartGroup.select(".x-axis")
                .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));
            // call(d3.axisBottom(x));
        }

        function applyXDomain(domain) {
            x.domain(domain);
            redrawLines();
            redrawXAxis();
            showLatestValues(true);

            // Clear brush without recursion
            chartGroup.select(".zoom").call(zoom.move, null);
        }
        // --- zoomOut ---
        function zoomOut() {
            applyXDomain(fullXDomain);
            chartGroup.select(".x-axis")
                .call(d3.axisBottom(x));
            hasZoomed = false;
            document.getElementById("resetZoomBtn").style.display = "none";
        }

        // ---------- BUILD LEGEND ----------
        legendContainer.selectAll("*").remove();

        // Legend styling
        // Build and style list of Boroughs in legend (data join)
        const legendItems = legendContainer
            .selectAll(".legend-item") //this line creates the css type item for each item in the legend
            .data(boroughs) //each item will be a different borough
            .enter()
            .append("div")
            .attr("class", "legend-item")
            .style("display", "flex") //styling
            .style("align-items", "center")
            .style("cursor", "pointer")
            .style("margin", "6px 0");


        // Colored circle
        legendItems.append("div")
            .style("width", "12px")
            .style("height", "12px")
            .style("border-radius", "50%")
            .style("margin-right", "8px")
            .style("background-color", d => color(d[0]));


        // Borough name
        legendItems.append("span")
            .text(d => d[0])
            .style("font-size", "13px");

        legendItems.on("click", (event, d) => {
            const clicked = d[0];

            if (activeBoroughs.has(clicked)) {
                // Already selected → unselect it
                unhighlightBoroughs(clicked);
            } else {
                // Not selected → add it
                highlightBoroughs(clicked);

            }
            showLatestValues();
        });


        let showDate = false;
        // HOVER LINE MOUSE EVENT LOGIC
        chartSVG.on("mousemove", function(event) {

            if (activeBoroughs.size === 0) return;

            // ⭐ Always re-read the selected metric
            const selectedMetric = d3.select("#perception-metric-select").property("value");

            // ⭐ Filter data to the current metric
            const filtered = data.filter(d => d.metric === selectedMetric);

            // ⭐ Group by borough for this metric
            const byBorough = d3.group(filtered, d => d.borough);
            const boroughsForMetric = Array.from(byBorough);

            // Use chartGroup as the coordinate reference
            const [mx] = d3.pointer(event, chartGroup.node());
            const rawDate = x.invert(mx);

            // ⭐ Snap to nearest real data point using FIRST active borough
            let snappedDate = rawDate;

            const firstBorough = boroughsForMetric.find(b => activeBoroughs.has(b[0]));
            if (firstBorough) {
                const closest = firstBorough[1].reduce((a, c) =>
                    Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
                );
                snappedDate = closest.date;
            }

            // ⭐ Move vertical hover line using snapped date
            const snappedX = x(snappedDate);
            hoverLine
                .attr("x1", snappedX)
                .attr("x2", snappedX)
                .style("opacity", 1);

            // ⭐ Build hover list using snapped date FOR THE CURRENT METRIC
            const hoverData = boroughsForMetric
                .filter(b => activeBoroughs.has(b[0]))
                .map(b => {
                    const closest = b[1].reduce((a, c) =>
                        Math.abs(c.date - snappedDate) < Math.abs(a.date - snappedDate) ? c : a
                    );
                    return {
                        borough: b[0],
                        metric_value: closest.metric_value,
                        metric_value_pct: closest.metric_value_pct,
                        date: closest.date
                    };
                });

            updateHoverList(snappedDate, hoverData, true);
        })
            .on("mouseleave", function() {
                hoverLine.style("opacity", 0);
                if (activeBoroughs.size > 0) {
                    // ⭐ Boroughs selected → show latest date again
                    showLatestValues(true);
                } else {
                    showLatestValues(false);   // your helper function
                }
            });


        // boroughLines.on("mousemove", function(event, d) {
        //
        //     if (!activeBoroughs.has(d[0])) {
        //         hideTooltip();
        //         return;
        //     }
        //
        //     const selectedMetric = d3.select("#perception-metric-select").property("value");
        //
        //     // Use chartGroup as reference (NOT the path element)
        //     const [mx] = d3.pointer(event, chartGroup.node());
        //     const rawDate = x.invert(mx);
        //
        //     // Snap to nearest date for THIS borough
        //     const closest = d[1].reduce((a, c) =>
        //         Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
        //     );
        //
        //     const dataPoint = closest;
        //
        //     showTooltip(event, {
        //         borough: d[0],
        //         metric_value: dataPoint.metric_value,
        //         metric_value_pct: dataPoint.metric_value_pct,
        //         date: dataPoint.date,
        //         selectedMetric: selectedMetric
        //     });
        //
        //     updateHoverList(dataPoint.date, [{
        //         borough: d[0],
        //         metric_value: dataPoint.metric_value,
        //         metric_value_pct: dataPoint.metric_value_pct
        //     }], true);
        // });

        document.getElementById("resetZoomBtn").addEventListener("click", zoomOut);

    })

}

