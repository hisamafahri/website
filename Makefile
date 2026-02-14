# What to compile by default?
SOURCES := $(shell find docs -name "*.md" -type f)
TARGETS := $(patsubst docs/%.md,dist/%.html,$(SOURCES))

STYLES := tufte.css \
	pandoc.css \
	pandoc-solarized.css \
	tufte-extra.css

.PHONY: all
all: $(TARGETS) docs

# Note: you will need pandoc 2 or greater for this to work

## Generalized rule: how to build a .html file from each .md
dist/%.html: docs/%.md tufte.html5 $(STYLES)
	mkdir -p $(dir $@)
	pandoc \
		--katex \
		--section-divs \
		--from markdown+tex_math_single_backslash \
		--lua-filter pandoc-sidenote.lua \
		--include-before-body navbar.html \
		--to html5+smart \
		--template=tufte \
		$(foreach style,$(STYLES),--css /$(notdir $(style))) \
		--output $@ \
		$< || \
	pandoc \
		--katex \
		--section-divs \
		--from markdown+tex_math_single_backslash \
		--include-before-body navbar.html \
		--to html5+smart \
		--template=tufte \
		$(foreach style,$(STYLES),--css /$(notdir $(style))) \
		--output $@ \
		$<

.PHONY: clean
clean:
	rm -rf dist

# The default tufte.css file expects all the assets to be in the same folder.
# In real life, instead of duplicating the files you'd want to put them in a
# shared "css/" folder or something, and adjust the `--css` flags to the pandoc
# command to give the correct paths to each CSS file.
.PHONY: docs
docs:
	mkdir -p dist/et-book dist/journals
	cp -r $(STYLES) dist/
	cp -r et-book dist/
	cp latex.css dist/journals/
	cp favicon.ico pgp.txt robots.txt rss.xml sitemap.xml dist/
