/*!
 * docc | GPL-3.0 License | https://github.com/SamWilsn/docc
 */
(function() {
    "use strict";

    const onLoad = () => {
        const searchBase = document.querySelector("meta[name='docc:search']");
        const searchPath = document.getElementById("search-path");
        const searchContainer = document.getElementById("search-results-container");
        const searchElement = document.getElementById("search-results");
        const mainElement = document.getElementById("main-content");

        const tag = document.createElement("script");
        tag.async = true;
        tag.src = searchPath.href;

        const searcherPromise = new Promise((resolve, reject) => {
            const onLoad = () => {
                tag.removeEventListener("load", onLoad);
                tag.removeEventListener("error", onError);

                const options = {
                    keys: [
                        "content.name",
                        {
                            name: "content.text",
                            weight: 0.75
                        },
                        {
                            name: "source.path",
                            weight: 0.5
                        }
                    ]
                };

                resolve(new Fuse(window.SEARCH_INDEX, options));
            };

            const onError = (e) => {
                tag.removeEventListener("load", onLoad);
                tag.removeEventListener("error", onError);
                reject(e);
            };

            tag.addEventListener("load", onLoad);
            tag.addEventListener("error", onError);

            document.body.appendChild(tag);
        });

        const bars = document.querySelectorAll(".search-bar input[type='search']");

        const clearSearch = () => {
            for (const bar of bars) {
                bar.value = "";
                const event = new Event('input', {
                    bubbles: true,
                    cancelable: true,
                });
                bar.dispatchEvent(event);
            }
        };

        const onTimeout = async (e) => {
            delete e.target.dataset.timeoutId;
            if (!e.target.value) {
                searchElement.replaceChildren();
                mainElement.style.display = "initial";
                searchContainer.style.display = "none";
                return;
            }

            const searcher = await searcherPromise;
            const results = searcher.search(e.target.value);

            mainElement.style.display = "none";
            searchContainer.style.display = "initial";
            searchElement.replaceChildren(...results.map((r) => {
                const href = new URL(
                    r.item.source.path + ".html",
                    new URL(searchBase.getAttribute("value"), window.location)
                );

                if (r.item.source.identifier) {
                    const specifier = r.item.source.specifier || 0;
                    href.hash = `#${r.item.source.identifier}:${specifier}`;
                }

                const anchor = document.createElement("a");
                anchor.innerText = r.item.content.name;
                anchor.href = href;
                anchor.addEventListener("click", clearSearch);

                const path = document.createElement("span");
                path.classList.add("search-path");
                path.innerText = " " + r.item.source.path

                const elem = document.createElement("li");
                elem.appendChild(anchor);
                elem.appendChild(path);

                if (r.item.content.text) {
                    const text = document.createElement("div");
                    text.classList.add("search-text");
                    text.innerText = " " + r.item.content.text;
                    elem.appendChild(text);
                }

                return elem;
            }));
        };

        const onInput = async (e) => {
            const timeoutIdText = e.target.dataset.timeoutId;
            if (timeoutIdText !== undefined) {
                const timeoutId = Number.parseInt(timeoutIdText);
                clearTimeout(timeoutId);
            }

            e.target.dataset.timeoutId = setTimeout(() => onTimeout(e), 300);
        };

        for (const bar of bars) {
            bar.addEventListener("input", onInput);
        }
    };

    if ("complete" === document.readyState) {
        onLoad();
    } else {
        window.addEventListener("DOMContentLoaded", onLoad);
    }
})();
