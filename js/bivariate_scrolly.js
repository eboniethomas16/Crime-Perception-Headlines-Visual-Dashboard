import { updateMap, mapReady,projection, path, sizeAndDraw,geo } from "./bivariate_choropleth_map.js";

// DOM selections
const scrolly = d3.select("#scrolly");
const article = scrolly.select("article");
const figure = scrolly.select("figure");
const step = article.selectAll(".step");

const scroller = scrollama();
const dateScroller = document.getElementById("quarterScroller");
const dateScrollerLabel = document.getElementById("quarter-scroller-label");
const legend = document.getElementById("legend");
const mapWrapper = document.getElementById("map-wrapper");
const LondonMap = document.getElementById("map");

// BOOLEAN CHECK VALUES FOR THE STEP ANIMATIONS
let hasAnimatedMapIntro = false;   // has the map intro animation ever run?
let hasPassedMapIntro = false;     // has the user scrolled past map-intro?
let hasAnimatedLegendIntro = false;
let hasPassedLegendIntro = false;

// USED TO RESIZE MAP WHEN WINDOW SIZE CHANGES
let baseWrapperWidth = null;
let baseWrapperHeight = null;
dateScroller.style.visibility = "hidden";
dateScrollerLabel.style.visibility = "hidden";
legend.style.visibility = "hidden";
async function init() {
    // Wait for map to finish loading
    await mapReady;

    // Now safe to initialize scrollama
    handleResize();

    scroller
        .setup({
            step: "#scrolly article .step",
            offset: 0.4,//step doesnt trigger until 0.5 = 50% of the screen is filled
            debug: false
        })
        .onStepEnter(handleStepEnter);

    sizeAndDraw();
    window.addEventListener("resize", handleResize);
}

init();

function handleResize() {
    // Step height - controls the height of the text on the left
    const stepHeight = Math.floor(window.innerHeight * 0.75);
    step.style("height", stepHeight + "px");

    // GitHub sticky-side logic
    const figureHeight = window.innerHeight / 2;
    const figureMarginTop = (window.innerHeight - figureHeight) / 2;

    figure
        .style("height", figureHeight + "px")
        .style("top", figureMarginTop + "px");
    resizeMap();
    scroller.resize();

}
function resizeMap() {
    //"d3.select("map")" does not change the raw DOM element
        //instead this allows me to
        // append the borough elements == "g"
        //run transitions
        //set SVG attributes
        //draw the map
    const LondonMap = d3.select("#map");
    const g = LondonMap.select("#borough-group");

    if (LondonMap.empty() || g.empty()) return; // map not drawn yet
    if (baseWrapperWidth === null || baseWrapperHeight === null) return;

    // Recompute fixed position
    const wrapperBox = mapWrapper.getBoundingClientRect();
    const mapOffsetX = wrapperBox.left - 150;
    const mapOffsetY = wrapperBox.top + 20;

    LondonMap
        .style("left", `${mapOffsetX}px`)
        .style("top", `${mapOffsetY}px`);

    const currentWidth = wrapperBox.width;
    const currentHeight = wrapperBox.height;

    // Dynamic scale relative to original size
    // ISSUE: CHANGING WINDOW STRETCHES THE MAP INSTEAD OF ENLARGING IT
    const baseScaleFactor = 3;
    const scaleFactorX = baseScaleFactor * (currentWidth / baseWrapperWidth);
    const scaleFactorY = baseScaleFactor * (currentHeight / baseWrapperHeight);
    g.attr("transform", `scale(${scaleFactorX}, ${scaleFactorY})`);

    // Use wrapper size (NOT map size!)
    // const mapWidth = wrapperBox.width;
    // const mapHeight = wrapperBox.height;

    // Reapply scale factor
    // const scaleFactor = 3;
    // g.attr("transform", `scale(${scaleFactor})`);


    // Resize SVG container
    LondonMap
        .attr("width", currentWidth * baseScaleFactor)
        .attr("height", currentHeight * baseScaleFactor);
    // LondonMap
    //     .attr("width", mapWidth * scaleFactor)
    //     .attr("height", mapHeight * scaleFactor);
}


function showMap() {
    const scaleFactor = 3;
    const LondonMap = d3.select("#map");
    // LondonMap.style.visibility = "visible";
    Object.assign(LondonMap.node().style, {
        opacity: "1",
        transform: "translateY(0px)",
        transition: "opacity 500ms ease-out, transform 500ms ease-out",
        pointerEvents: "auto"
    });

    // Remove old paths + groups
    LondonMap.selectAll("*").remove();

    // Create a group for boroughs
    const g = LondonMap.append("g").attr("id", "borough-group");

    const currentPath = path;

    // Get bounding boxes
    const wrapperBox = mapWrapper.getBoundingClientRect();

    // Save the initial wrapper size for scaling later
    baseWrapperWidth = wrapperBox.width;
    baseWrapperHeight = wrapperBox.height;

    // Position the map SVG itself
    const mapOffsetX = wrapperBox.left - 150;
    const mapOffsetY = wrapperBox.top + 20;

    LondonMap
        .style("position", "fixed")
        .style("left", `${mapOffsetX}px`)
        .style("top", `${mapOffsetY}px`);

    // Recompute map box after positioning
    const mapWidth = wrapperBox.width;
    const mapHeight = wrapperBox.height;

    // Random scatter positions
    const randomX = () => Math.random() * mapWidth;
    const randomY = () => Math.random() * mapHeight;

    // Draw boroughs in random positions
    const boroughs = g.selectAll("path")
        .data(geo.features)
        .join("path")
        .attr("class", "borough")
        .attr("fill", "#c4addc")
        .attr("opacity", 0)
        .attr("transform", d => `translate(${randomX()}, ${randomY()})`)
        .attr("d", currentPath);

    // Animate into correct positions
    boroughs.transition()
        .duration(1200)
        .delay((d, i) => i * 10)
        .attr("opacity", 1)
        .attr("transform", "translate(0,0)");

    // Scale the individual boroughs
    g.attr("transform", `scale(${scaleFactor})`);

    // Resize the SVG container to keep in sc
    LondonMap
        .attr("width", mapWidth * scaleFactor)
        .attr("height", mapHeight * scaleFactor);
}
function hideMap() {
    Object.assign(LondonMap.style, {
        opacity: "0",
        transform: "translateY(20px) scale(0.95)",
        transition: "opacity 400ms ease-in, transform 400ms ease-in",
        pointerEvents: "none"
    });
}

function positionLeftArrowWrapper() {
    const wrapper = document.querySelector(".left-arrow-wrapper");
    const legendSvg = document.getElementById("legend");

    // Convert NodeList → Array
    const squares = Array.from(legendSvg.querySelectorAll("rect"));
    if (!squares.length) return;

    // Find max x (rightmost column)
    const maxX = Math.max(...squares.map(r => parseFloat(r.getAttribute("x"))));

    // Find min y (top row)
    const minY = Math.min(...squares.map(r => parseFloat(r.getAttribute("y"))));

    // Find the rect that matches both
    const topRightSquare = squares.find(rect => {
        const x = parseFloat(rect.getAttribute("x"));
        const y = parseFloat(rect.getAttribute("y"));
        return x === maxX && y === minY;
    });

    if (!topRightSquare) return;

    const box = topRightSquare.getBoundingClientRect();

    // Your arrow math (kept exactly as your original style)
    const x = box.right + 70;
    const y = box.top + box.height;

    wrapper.style.position = "fixed";
    wrapper.style.left = `${x}px`;
    wrapper.style.top = `${y}px`;
}


function positionRightArrowWrapper() {
    const wrapper = document.querySelector(".right-arrow-wrapper");
    const legendSvg = document.getElementById("legend");

    // Convert NodeList → Array
    const squares = Array.from(legendSvg.querySelectorAll("rect"));
    if (!squares.length) return;

    // Find min x (leftmost column)
    const minX = Math.min(...squares.map(r => parseFloat(r.getAttribute("x"))));

    // Find max y (bottom row)
    const maxY = Math.max(...squares.map(r => parseFloat(r.getAttribute("y"))));

    // Find the rect that matches both
    const bottomLeftSquare = squares.find(rect => {
        const x = parseFloat(rect.getAttribute("x"));
        const y = parseFloat(rect.getAttribute("y"));
        return x === minX && y === maxY;
    });

    if (!bottomLeftSquare) return;

    const box = bottomLeftSquare.getBoundingClientRect();

    // Your arrow math stays EXACTLY as you wrote it
    const arrowX = box.left - 80;
    const arrowY = box.top + box.height + 25;

    wrapper.style.position = "fixed";
    wrapper.style.left = `${arrowX}px`;
    wrapper.style.top = `${arrowY}px`;
}


function showArrows() {
    positionLeftArrowWrapper();
    positionRightArrowWrapper();

    document.querySelector(".left-arrow-wrapper").style.opacity = "1";
    document.querySelector(".left-arrow-wrapper").style.transform = "translate(-50%, -50%) scale(2)";

    document.querySelector(".right-arrow-wrapper").style.opacity = "1";
    document.querySelector(".right-arrow-wrapper").style.transform = "translate(-50%, -50%) scale(2)";
}

function hideArrows() {
    document.querySelector(".left-arrow-wrapper").style.opacity = "0";
    document.querySelector(".left-arrow-wrapper").style.transform = "translate(-50%, -50%) scale(0.8)";

    document.querySelector(".right-arrow-wrapper").style.opacity = "0";
    document.querySelector(".right-arrow-wrapper").style.transform = "translate(-50%, -50%) scale(0.8)";
}

function moveLegendCenter() {
    const rect = mapWrapper.getBoundingClientRect();

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    legend.style.visibility = "visible";

    // Reset AOS so animation can run again
    legend.classList.remove("aos-animate");
    legend.classList.remove("aos-init");
    void legend.offsetWidth;

    legend.setAttribute("data-aos", "zoom-in");
    legend.setAttribute("data-aos-duration", "600"); // 1.2 seconds
    legend.setAttribute("data-aos-anchor", "#trigger-legend-intro");


    legend.classList.add("aos-animate");

    // Move legend to wrapper center
    legend.style.position = "fixed"; // stays relative to viewport
    legend.style.left = `${centerX}px`;
    legend.style.top = `${centerY}px`;
    legend.style.transform = "translate(-50%, -50%) scale(3)";
}

function moveLegendRight() {
    const wrapperBox = mapWrapper.getBoundingClientRect();

    const rightX = wrapperBox.right - 400; // adjust padding
    const topY = wrapperBox.top + 100;

    void legend.offsetWidth;

    legend.setAttribute("data-aos", "slide-right");
    legend.setAttribute("data-aos-easing", "ease-out-cubic");
    legend.setAttribute("data-aos-anchor", "#trigger-map-intro");

    // void legend.offsetWidth;
    legend.classList.add("aos-animate");

    legend.style.position = "fixed";
    legend.style.left = `${rightX}px`;
    legend.style.top = `${topY}px`;
    legend.style.transform = "translate(0, 0) scale(2)";
}
function showDateScroller() {
    dateScroller.style.visibility = "visible";
    dateScrollerLabel.style.visibility = "visible";
    Object.assign(dateScroller.style, {
        opacity: "1",
        transform: "translateY(0)",
        pointerEvents: "auto"
    });

    Object.assign(dateScrollerLabel.style, {
        opacity: "1",
        transform: "translateY(0)",
        pointerEvents: "auto"
    });
}


function hideDateScroller() {
    Object.assign(dateScroller.style, {
        opacity: "0",
        transform: "translateY(20px)",
        pointerEvents: "none"
    });

    Object.assign(dateScrollerLabel.style, {
        opacity: "0",
        transform: "translateY(20px)",
        pointerEvents: "none"
    });
}

// CONTROLS WHAT IS SEEN AS SOON AS PAGE IS LOADED
// AND WHAT IS SHOWN AS USER SCROLLS THROUGH EACH STEP
function handleStepEnter(response) {
    const el = response.element;
    const stepType = el.dataset.step;
    const metric = el.dataset.metric;

    // Highlight active step
    d3.selectAll(".step").classed("is-active", false);
    d3.select(el).classed("is-active", true);

    // STEP 0 - INTRO — everything hidden
    if (stepType === "intro") {
        // Fully hide legend
        legend.hidden = true;
        legend.style.visibility = "hidden";
        // Hide the date scroller
        hideDateScroller();
        hideMap();

        // FULL AOS RESET
        legend.classList.remove("aos-animate");
        legend.classList.remove("aos-init");
        void legend.offsetWidth; // force reflow

        d3.select("#controls").classed("hidden", true);

        // d3.select("#map").classed("hidden", true);

        // Reset state if user scrolls all the way back to the top
        hasPassedMapIntro = false;
        hasAnimatedMapIntro = false;
        hasPassedLegendIntro = false;
        hasAnimatedLegendIntro = false;
        return;
    }
    // LEGEND INTRO
    if (stepType === "legend-intro") {
        hideArrows();

        legend.hidden = false;
        hideDateScroller();
        hideMap();
        // ALWAYS animate legend back to center
        moveLegendCenter();
        hasAnimatedLegendIntro = true;
        hasPassedLegendIntro = false;
        hasPassedMapIntro = false;
        hasAnimatedMapIntro = false
        return;
    }
    // LEGEND INSTRUCTIONS
    if (stepType === "legend-instruction") {
        // Legend stays visible and centered
        legend.hidden = false;
        moveLegendCenter();

        // Keep map hidden
        hideMap();

        // Keep controls hidden
        hideDateScroller();
        // delay hiding controls until animation finishes
        setTimeout(() => {
            d3.select("#controls").classed("hidden", true);
            showArrows();
        }, 601); // match hide animation duration

        hasPassedMapIntro = false;
        hasAnimatedMapIntro = false
        return;
    }
    // 3. MAP INTRO
    if (stepType === "map-intro") {
        showDateScroller();
        moveLegendRight();
        hideArrows();

        d3.select("#controls").classed("hidden", false);

        // Mark that user has passed legend intro
        hasPassedLegendIntro = true;

        // Run map animation only if:
            //map was not previously on screen
        if (!hasAnimatedMapIntro && !hasPassedMapIntro) {
            showMap();
            hasAnimatedMapIntro = true;
        }
        // CASE 3: User scrolls UP into map-intro AFTER passing it
        // → DO NOTHING (no reanimation)
        return;
    }

    // ANY OTHER STEP BELOW MAP-INTRO
    // Means user has passed map-intro at least once
    hasPassedMapIntro = true;
    if (metric) {
        d3.select("#controls").classed("hidden", false);

        moveLegendRight(); // keep legend docked right

        updateMap(metric);
    }
}