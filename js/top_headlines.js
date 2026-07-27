export function drawTopHeadlinesChart(chart_TopHeadlines, list_hoverListContainer) {

    const chartContainer = d3.select(chart_TopHeadlines);
    const hoverListContainer = d3.select(list_hoverListContainer);
    const tooltip = d3.select("#tooltip");
    const resetZoomBtn = d3.select("#resetZoomBtn");

    hoverListContainer.attr("class", "hover-list");



    // ------------------------------------------------------------
    // STREAMGRAPH FUNCTION
    // ------------------------------------------------------------
    async function drawTopHeadlinesStreamgraph(container) {
        // STATE VARIABLES (shared across functions)
        let currentStackedData = null;
        let currentGrouped = null;
        let currentMode = "month";
        let currentZoomDomain = null;


        // const width = 900;
        // const height = 450;
        // const innerWidth = width - margin.left - margin.right;
        // const innerHeight = height - margin.top - margin.bottom;
        const margin = {top: 20, right: 40, bottom: 40, left: 60};
        const width = 900 - margin.left - margin.right;
        const height = 600 - margin.top - margin.bottom;

        // ---------- SVG ----------
        const chartSVG = d3.select(container)
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);


        // ---------- CHART GROUP ----------
        const chartGroup = chartSVG.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        // ---------- CLIP PATH ----------
        chartGroup.append("defs")
            .append("clipPath")
            .attr("id", "clip")
            .append("rect")
            .attr("width", width)
            .attr("height", height);

        // ---------- PLOT GROUP ----------
        const plotGroup = chartGroup.append("g")
            .attr("clip-path", "url(#clip)")


        // HOVER LINE
        const hoverLine = chartGroup.append("line")
            .attr("class", "hover-line")
            .attr("y1", 0)
            .attr("y2", height)
            .style("opacity", 0);


        // ------------------------------------------------------------
        // LOAD FINAL MERGED CSV
        // ------------------------------------------------------------
        const data = await d3.csv("../data/headline_daily_monthly_summary.csv", d3.autoType);

        data.forEach(d => {
            d.Month = new Date(d.Month);
            d.Day = d.Day ? new Date(d.Day) : null;
        });

        const rankColor = {
            1: "#4e79a7",
            2: "#f28e2b",
            3: "#e15759"
        };

        // ------------------------------------------------------------
        // DEFINE SCALES (structure only)
        // ------------------------------------------------------------
        const x = d3.scaleTime().range([0, width]);
        const y = d3.scaleLinear()
            .range([height, 0]);

        // ---------- AXIS GROUPS (created once) ----------

        // X scale
        // const fullXDomain = d3.extent(data.filter(d => d.Top_Month), d => d.Month);
        //
        // const x = d3.scaleTime()
        //     .domain(fullXDomain)
        //     .range([0, innerWidth]);

        chartGroup.append("g")
            .attr("class", "x-axis")
            .attr("transform", `translate(0,${height})`)
        // .call(d3.axisBottom(x));


        // Y scale
        // const y = d3.scaleLinear()
        //     .domain([0, d3.max(data, d => d.count_month)])  // or dynamic
        //     .range([innerHeight, 0]);

        chartGroup.append("g")
            .attr("class", "y-axis")
        // .call(d3.axisLeft(y));


        // HOVER LINE MOUSEMOVE LOGIC
        chartSVG.on("mousemove", function (event) {

            // 1. Get mouse position relative to chartGroup
            const [mx] = d3.pointer(event, chartGroup.node());

            // If mouse is outside the plot area, hide the line
            if (mx < 0 || mx > width) {
                hoverLine.style("opacity", 0);
                return;
            }

            // 2. Convert pixel → raw date
            const rawDate = x.invert(mx);

            // 3. Snap to nearest real date in currentGrouped
            const closest = currentGrouped.reduce((a, b) =>
                Math.abs(b.date - rawDate) < Math.abs(a.date - rawDate) ? b : a
            );
            const snappedDate = closest.date;

            // 4. Convert snapped date → pixel
            const snappedX = x(snappedDate);

            // 5. Move vertical hover line
            hoverLine
                .attr("x1", snappedX)
                .attr("x2", snappedX)
                .style("opacity", 1);
            // 6. Build tooltip data for ALL ranks at this date
            const rows = closest.rows;
            if (!rows) {
                hideTooltip();
                return;
            }

            // Example: show rank 1 headline (you can expand this)
            const sorted = rows
                .slice()
                .sort((a, b) =>
                    (currentMode === "month"
                        ? a.Rank_Month - b.Rank_Month
                        : a.Rank_Day - b.Rank_Day)
                );

            // Build tooltip-friendly objects
            const tooltipData = sorted
                .filter(r => {
                    const rank = currentMode === "month" ? r.Rank_Month : r.Rank_Day;
                    return rank !== null && rank !== undefined;
                })
                .map(r => ({
                    headline: r.headline,
                    rank: currentMode === "month" ? r.Rank_Month : r.Rank_Day,
                    count: currentMode === "month" ? r.count_month : r.count_day
                }));


            showTooltip(event, {
                date: snappedDate,
                items: tooltipData
            });
        })
            .on("mouseleave", function () {
                hoverLine.style("opacity", 0);
                hideTooltip();

                // OPTIONAL: update hover list
                // updateHoverList(snappedDate);
            });


        // ------------------------------------------------------------
        // COMPUTE STREAMGRAPH DATA
        // ------------------------------------------------------------
        function computeStreamgraphData(filtered, mode) {

            const xField = mode === "month" ? "Month" : "Day";
            const yField = mode === "month" ? "count_month" : "count_day";
            const rankField = mode === "month" ? "Rank_Month" : "Rank_Day";


            const grouped = d3.groups(filtered, d => d[xField])
                .map(([date, rows]) => ({
                    date,
                    rows: rows
                        .filter(r => r[rankField] != null)   // ⭐ remove null ranks
                        .filter((r, idx, arr) =>
                            arr.findIndex(x => x[rankField] === r[rankField]) === idx
                        ) // ⭐ remove duplicate ranks
                }))
                .sort((a, b) => a.date - b.date);

            const stack = d3.stack()
                .keys([1, 2, 3])
                .value((rows, key) => {
                    const row = rows.find(r => r[rankField] === key);
                    return row ? row[yField] : 0;
                })
                .offset(d3.stackOffsetNone)
            // .offset(d3.stackOffsetWiggle);


            const stackedData = stack(grouped.map(g => g.rows));
            console.log("STACKED", JSON.stringify(stackedData));


            // Update scales
            // Compute total headlines per date
            const totals = grouped.map(g => {
                return d3.sum(g.rows, r => r[yField] || 0);
            });

            // Set y-domain based on raw totals
            x.domain(d3.extent(grouped, d => d.date));
            y.domain([0, d3.max(totals)]);

            // create static y-axis
            chartGroup.select(".y-axis")
                .call(
                    d3.axisLeft(y)
                        .ticks(10)     // clean tick spacing
                );

            currentGrouped = grouped;
            currentStackedData = stackedData;
        }

        // ------------------------------------------------------------
        // DRAW STREAMGRAPH (initial)
        // ------------------------------------------------------------
        function drawStreamgraph() {

            const area = d3.area()
                .x((d, i) => x(currentGrouped[i].date))
                .y0(d => y(d[0]))
                .y1(d => y(d[1]))
                .curve(d3.curveMonotoneX);

            // Clear plot area
            plotGroup.selectAll("*").remove();

            // Draw streamgraph layers
            plotGroup.selectAll("path")
                .data(currentStackedData)
                .join("path")
                .attr("class", "stream-layer")
                .attr("d", area)
                .attr("fill", (d, i) => rankColor[i + 1])
                .attr("opacity", 0.9)

            // Update axes
            chartGroup.select(".x-axis")
                .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));


        }


        // ------------------------------------------------------------
        // UPDATE STREAMGRAPH (zoom/brush)
        // ------------------------------------------------------------
        function updateStreamgraph() {

            const area = d3.area()
                .x((d, i) => x(currentGrouped[i].date))
                .y0(d => y(d[0]))
                .y1(d => y(d[1]))
                .curve(d3.curveMonotoneX);

            plotGroup.selectAll("path")
                .data(currentStackedData)
                .join("path")
                .attr("d", area);

            chartGroup.select(".x-axis")
                .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%b %Y")));

            chartGroup.select(".y-axis")
                .call(d3.axisLeft(y));

            // Clear brush without recursion
            chartGroup.select(".zoom").call(zoomBrush.move, null);
        }

        // ------------------------------------------------------------
        // CALL TO CREATE INITIAL MONTHLY VIEW
        // ------------------------------------------------------------
        computeStreamgraphData(data.filter(d => d.Top_Month), "month");
        drawStreamgraph();
        updateHoverListHeadlines(); // ⭐ show top 10 immediately

        // Save full domain for reset
        const fullXDomain = x.domain();
        // ------------------------------------------------------------
        // BRUSH ZOOM
        // ------------------------------------------------------------
        const zoomBrush = d3.brushX()
            .extent([[0, 0], [width, height]])
            .on("end", zoomIn);

        chartGroup.append("g")
            .attr("class", "zoom")
            .call(zoomBrush);


        // ------------------------------------------------------------
        // TOOLTIP FUNCTIONS (your originals)
        // ------------------------------------------------------------
        function showTooltip(event, d) {
            const dateStr = d3.timeFormat("%b %Y")(d.date);

            // Build the list of ranked headlines
            const listHTML = d.items.map(item => `
            <div style="color:${rankColor[item.rank]}; margin: 4px 0;">
                <strong>${item.rank}. ${item.headline}</strong><br>
                published <strong>${item.count}</strong> times
            </div>
            `).join("");

            tooltip.style("opacity", 1)
                .html(`
                    <div style="
                        font-weight:700;
                        text-align:center;
                        margin-bottom:6px;
                        font-size:13px;
                    ">
                        ${dateStr}
                    </div>
        
                    <div style="font-size:12px;">
                        ${listHTML}
                    </div>
                `)
                .style("left", (event.pageX + 12) + "px")
                .style("top", (event.pageY + 12) + "px");
        }

        function hideTooltip() {
            tooltip.style("opacity", 0);
        }

        function updateHeadlineList(headlines) {
            // Clear previous content
            hoverListContainer.selectAll("*").remove();

            if (!headlines || headlines.length === 0) {
                hoverListContainer
                    .style("opacity", 0)
                    .style("display", "none");
                return;
            }

            hoverListContainer
                .style("opacity", 1)
                .style("overflow-y", "auto")
                .style("display", "inline-block")
                .style("flex-direction", "column")
                .style("max-height", `${height}px`)
                .style("width", `550px`) //Can change depending on the window
                .style("margin-left", `20px`)
                .style("margin-bottom", `8px`)
                .style("vertical-align", "top")
            ;

            // Header
            hoverListContainer
                .append("div")
                .style("font-weight", "600")
                .style("text-align", "center")
                .style("align-items", "center")
                .text("Top Headlines Between");

            // Date range underneath
            hoverListContainer
                .append("div")
                .style("text-align", "center")
                .style("font-weight", "600")
                .style("margin-bottom", "12px")
                .style("text-decoration", "underline")
                // .style("font-size", "14px")
                .text(headlines[0].range);

            // Ordered list container
            const list = hoverListContainer
                .append("ol")
                .style("padding-left", "20px")   // indent like a real list
                .style("margin", "0")
                .style("width", "100%");

            // Rows (li items)
            const rows = list
                .selectAll("li")
                .data(headlines)
                .join("li")
                .attr("class", "hover-row")
                .style("margin", "8px 0")
                .style("text-align", "left");

            rows.html((d, i) =>
                `${d.headline}: <strong>Republished ${d.count} times</strong> 
                 <a href="${d.link}" target="_blank" 
                    style=color:#3366cc; text-decoration:underline;">
                    (read article)
                 </a>`
                        );

        }


        function zoomIn(event) {
            if (!event.sourceEvent) return;   // ignore programmatic brush moves
            const selection = event.selection;

            // If brush is cleared → reset zoom
            // if (!selection) {
            //     x.domain(fullXDomain);
            //     currentZoomDomain = null;   // ⭐ clear zoom domain
            //     updateStreamgraph();
            //     resetZoomBtn.style("display", "none");
            //
            //     // clear hover list
            //     updateHeadlineList([]);
            //     return;
            // }

            // Convert pixel range → date range
            const [x0, x1] = selection;
            const newDomain = [x.invert(x0), x.invert(x1)];

            // ⭐ Save zoom x-range domain globally
            currentZoomDomain = newDomain;

            // Apply new domain
            x.domain(newDomain);

            // Redraw streamgraph + axes
            updateStreamgraph();

            // Show reset button
            resetZoomBtn.style("display", "inline-block");
            // Update hover list
            updateHoverListHeadlines()
        }


        function zoomOut() {
            // Restore full domain
            x.domain(fullXDomain);
            currentZoomDomain = fullXDomain;

            // Redraw streamgraph + axes
            updateStreamgraph();

            // Hide reset button
            resetZoomBtn.style("display", "none");

            updateHoverListHeadlines();
        }

        function updateHoverListHeadlines() {
            // Decide which fields to use based on currentMode
            const xField   = currentMode === "month" ? "Month"      : "Day";
            const yField   = currentMode === "month" ? "count_month": "count_day";
            const rankField= currentMode === "month" ? "Rank_Month" : "Rank_Day";
            // Determine the date range to use
            let startDate, endDate;

            if (currentZoomDomain) {
                // Use zoomed range
                [startDate, endDate] = currentZoomDomain;
            } else {
                // Use full current domain (safe even before fullXDomain is set)
                const domain = x.domain();
                startDate = domain[0];
                endDate = domain[1];
            }

            const rangeLabel = `${d3.timeFormat("%B %Y")(startDate)} - ${d3.timeFormat("%B %Y")(endDate)}`;


            // Filter raw data to the selected range
            const filteredRange = data.filter(d => {
                const date = currentMode === "month" ? d.Month : d.Day;
                return date >= startDate && date <= endDate;
            });

            // Sort by count
            const sorted = filteredRange
                .filter(d => d[rankField] != null)
                .sort((a, b) => b[yField] - a[yField]);

            // Top 10
            const top10 = sorted.slice(0, 10).map(d => ({
                headline: d.headline,
                count: d[yField],
                rank: d[rankField],
                link: d["Headline_Source"],
                range: rangeLabel
            }));

            updateHeadlineList(top10);
        }



        resetZoomBtn.on("click", zoomOut);

            // computeStreamgraphData(data.filter(d => d.Top_Month), "month");
            // drawStreamgraph();
    }
    drawTopHeadlinesStreamgraph(chartContainer.node());
}
