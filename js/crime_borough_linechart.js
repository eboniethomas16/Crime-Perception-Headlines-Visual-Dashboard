// Chart module
// → reusable function that draws the chart anywhere
// js/crime_borough_linechart.js

export function drawBoroughChart(chart_crimeBorough, legend_crimeBorough) {

    // POSITION THE CHART + LEGEND SIDE BY SIDE
    // Position chart + legend side-by-side
    const chartContainer = d3.select(chart_crimeBorough);
    const legendContainer = d3.select(legend_crimeBorough);
    const tooltip = d3.select("#tooltip");
    const hoverListContainer = d3.select("#crime-borough-hoverlist");

    let activeBoroughs = new Set();


// Apply layout styles directly
    chartContainer
        .style("display", "inline-block")
        .style("vertical-align", "top");


    //positions it to the right of legend
    hoverListContainer
        .attr("class", "hover-list")

    // Load data
    d3.csv("../data/crime_borough_monthly.csv").then(data => {

        // Parse date
        const parseOriginal = d3.timeParse("%m/%d/%Y");   // matches your raw data
        const formatMonthYear = d3.timeFormat("%b-%Y");   // "Jan-2015"
        const parseMonthYear = d3.timeParse("%b-%Y");     // final Date object

        data.forEach(d => {
            const raw = parseOriginal(d.date);  // parse "1/1/2015"

            if (!raw) {
                console.warn("Bad date:", d.date);
                return;
            }

            const monthYearString = formatMonthYear(raw);  // "Jan-2015"
            d.date = parseMonthYear(monthYearString);      // Date object for Jan 2015

            d.crime_count = +d.crime_count;
        });
        // ---------- FILTER TO >= APRIL 2017 ----------
        const cutoff = new Date(2017, 3, 1);   // month index 3 = April
        data = data.filter(d => d.date >= cutoff);

        // Group by borough
        const boroughs = d3.groups(data, d => d.borough);

        // Get the most recent date on screen
        const latestDate = d3.max(data, d => d.date);

        // ---------- CHART DIMENSIONS ----------
        const margin = { top: 1, right: 40, bottom: 40, left: 60 };
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
            .style("opacity", 0);

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
            .domain([0, d3.max(data, d => d.crime_count)])
            .range([height, 0]);
        chartGroup.append("g")
            .call(d3.axisLeft(y));


        // Color scale
        const color = d3.scaleOrdinal()
            .domain(boroughs.map(d => d[0]))
            .range(d3.schemeTableau10);

        legendContainer.style

        // ---------- DRAW LINES ----------
        const lineGen = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.crime_count));

        // Draw lines
        const boroughLines = chartGroup.selectAll(".lines")
            .data(boroughs)
            .enter()
            .append("path")
            .attr("class", "lines")
            .attr("clip-path", "url(#clip)") //clips lines
            .attr("d", d => lineGen(d[1]))
            .attr("stroke", d => color(d[0]))
            .attr("fill", "none");

        // ---------- ZOOM OBJECT ----------
        const zoom = d3.brushX()
            .extent([[0, 0], [width, height]])
            .on("end", zoomIn);

        const brushGroup = chartGroup.append("g")
            .attr("class", "zoom")
            .call(zoom);
        brushGroup.raise();

        // ---------- LEGEND HIGHLIGHT INTERACTION ----------

        function highlightBoroughs(selected) {
            activeBoroughs.add(selected);

            boroughLines
                .classed("highlighted", l => activeBoroughs.has(l[0]))
                .classed("dimmed", l => !activeBoroughs.has(l[0]));

            // Bring selected lines to front
            boroughLines.filter(l => activeBoroughs.has(l[0])).raise();

            // Legend dimming
            legendItems.style("opacity", l => activeBoroughs.has(l[0]) ? 1 : 0.4);

            showLatestValues(true);   // When a borough is selected, show latest date
        }

        function unhighlightBoroughs(selected) {
            activeBoroughs.delete(selected);

            boroughLines.classed("highlighted", l => activeBoroughs.has(l[0]));

            // If nothing selected → full reset
            if (activeBoroughs.size === 0) {
                resetHighlights();
                return;
            }

            // Otherwise update remaining highlights
            boroughLines.transition().duration(300)
                .attr("opacity", l => activeBoroughs.has(l[0]) ? 1 : 0.1)
                .attr("stroke-width", l => activeBoroughs.has(l[0]) ? 4 : 1.5);

            boroughLines.filter(l => activeBoroughs.has(l[0])).raise();

            legendItems.style("opacity", l => activeBoroughs.has(l[0]) ? 1 : 0.4);

            updateHoverList(null, [], false);
        }

        function resetHighlights() {
            activeBoroughs.clear();

            boroughLines
                .classed("highlighted", false)
                .classed("dimmed",false)
                .transition().duration(300)
                .attr("opacity", 0.9)
                .attr("stroke-width", 2);

            legendItems.style("opacity", 1);

            // Clear hover list completely
            updateHoverList(null, [], false);
        }

        function showTooltip(event, d) {
            tooltip.style("opacity", 1)
                .html(`
            <div style="font-weight:600;">${d.borough}</div>
            <div>Crime Count: <strong>${d.crime_count.toLocaleString()}</strong></div>
            <div>Date: <strong>${d3.timeFormat("%b %Y")(d.date)}</strong></div>
        `)
                .style("left", (event.pageX + 12) + "px")
                .style("top", (event.pageY + 12) + "px");
        }

        function hideTooltip() {
            tooltip.style("opacity", 0);
        }

        // ---------- HOVER LIST UPDATING ----------
        function updateHoverList(date, boroughDataArray, showDate = true) {
            // Clear previous content
            hoverListContainer.selectAll("*").remove();

            if (!boroughDataArray || boroughDataArray.length === 0) {
                return;   // nothing else should be drawn
            }

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
                        .call(addHoverRowListeners),   // ⭐ attach listeners here
                    update => update.call(addHoverRowListeners), // ⭐ reattach safely
                    exit => exit.remove()
                );

            // Colored circle
            hoverListRows.append("div")
                .style("width", "12px")
                .style("height", "12px")
                .style("border-radius", "50%")
                .style("margin-right", "8px")
                .style("background-color", d => color(d.borough));

            // Borough name + crime count
            hoverListRows.append("span")
                .html(d => `${d.borough}: <strong>${d.crime_count.toLocaleString()}</strong>`);

        }

        function addHoverRowListeners(selection) {
            selection
                .on("mouseover", (event, d) => {
                    const boroughName = d.borough;

                    boroughLines
                        .filter(l => l[0] === boroughName)
                        .classed("hover-highlight", true);
                })
                .on("mouseout", (event, d) => {
                    const boroughName = d.borough;

                    boroughLines
                        .filter(l => l[0] === boroughName)
                        .classed("hover-highlight", false);
                });
        }

        // build the list for the latest date
        function showLatestValues(showDate = true) {
            // Build array of highlighted boroughs at the latest date
            const latestData = boroughs
                .filter(b => activeBoroughs.has(b[0]))
                .map(b => {
                    const last = b[1][b[1].length - 1];   // last row for this borough
                    return {
                        borough: b[0],
                        crime_count: last.crime_count,
                        date: last.date
                    };
                });

            updateHoverList(latestDate, latestData, showDate);
        }

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

        console.log(chartSVG.node());
        let showDate = false;
        chartSVG.on("mousemove", function(event) {

            // Use chartGroup as the coordinate reference
            const [mx] = d3.pointer(event, chartGroup.node());
            const rawDate = x.invert(mx);

            // ⭐ Snap to nearest real data point using your existing reduce()
            // We use the FIRST highlighted borough to determine the snapped date
            let snappedDate = rawDate;

            if (activeBoroughs.size > 0) {
                const firstBorough = boroughs.find(b => activeBoroughs.has(b[0]));
                if (firstBorough) {
                    const closest = firstBorough[1].reduce((a, c) =>
                        Math.abs(c.date - rawDate) < Math.abs(a.date - rawDate) ? c : a
                    );
                    snappedDate = closest.date;
                }
            }

            // ⭐ Move vertical hover line using snapped date
            const snappedX = x(snappedDate);
            hoverLine
                .attr("x1", snappedX)
                .attr("x2", snappedX)

                .style("opacity", 1);

            // ⭐ Build hover list using snapped date (same as tooltip)
            if (activeBoroughs.size > 0) {

                const hoverData = boroughs
                    .filter(b => activeBoroughs.has(b[0]))
                    .map(b => {
                        const closest = b[1].reduce((a, c) =>
                            Math.abs(c.date - snappedDate) < Math.abs(a.date - snappedDate) ? c : a
                        );
                        return {
                            borough: b[0],
                            crime_count: closest.crime_count,
                            date: closest.date
                        };
                    });

                updateHoverList(snappedDate, hoverData, true);
            }
        })
            .on("mouseleave", function() {
                hideTooltip();
                hoverLine.style("opacity", 0);
                if (activeBoroughs.size > 0) {
                    // ⭐ Boroughs selected → show latest date again
                    showLatestValues(true);
                } else {
                showLatestValues(false);   // your helper function
                }
            });


        boroughLines // TOOLTIP FUNCTIONALITY
            .on("mousemove", function(event, d) {
                // Only show tooltip for highlighted boroughs
                if (!activeBoroughs.has(d[0])) {
                    hideTooltip();
                    return;
                }

                // Find nearest data point based on mouse position
                const [mx] = d3.pointer(event, this);
                const date = x.invert(mx);

                // Find the closest record in this borough’s dataset
                const dataPoint = d[1].reduce((a, b) =>
                    Math.abs(b.date - date) < Math.abs(a.date - date) ? b : a
                );

                showTooltip(event, {
                    borough: d[0],
                    crime_count: dataPoint.crime_count,
                    date: dataPoint.date
                });

            })
            .on("mouseleave", function() {
                hideTooltip();
                hoverLine.style("opacity", 0);

                if (activeBoroughs.size > 0) {
                    showLatestValues(true);   // Rule 2: show latest date
                } else {
                    updateHoverList(null, [], false);   // Rule 1: no date
                }
            });
        document.getElementById("resetZoomBtn").addEventListener("click", zoomOut);

        // hoverListRows
        //     .on("mouseover", (event, d) => {
        //         const boroughName = d.borough;
        //
        //         boroughLines
        //             .filter(l => l[0] === boroughName)
        //             .classed("hover-highlight", true);
        //     })
        //     .on("mouseout", (event, d) => {
        //         const boroughName = d.borough;
        //
        //         boroughLines
        //             .filter(l => l[0] === boroughName)
        //             .classed("hover-highlight", false);
        //     });

    })

}




// Add labels at end of each line
// svg.selectAll(".label")
//     .data(boroughs)
//     .enter()
//     .append("text")
//     .attr("class", "label")
//     .attr("transform", d => {
//         const last = d[1][d[1].length - 1];
//         return `translate(${x(last.date)},${y(last.crime_count)})`;
//     })
//     .attr("x", 5)
//     .attr("dy", "0.35em")
//     .style("font-size", "12px")
//     .text(d => d[0]);
