# Document Generation

In order to generate documentation for the DNA Workflows project we are using a mixture of ```mkdocs``` and ```pydoc-markdown``` which can both both installed locally using pip;

```
pip3 install pydoc-markdown
pip3 install mkdocs
```

Static page documentation is created in Markdown format and stored in ```./docs``` along with the configuration file for ```pydoc-markdown```.

```pydoc-markdown``` creates a wrapper for generating the ```mkdocs``` configuration whilst at the same time generating documentation from the python doc strings in the DNA Workflows modules.

The workflow for updating the documentation [here](https://wwwin-github.cisco.com/pages/cunningr/dna_workflows/) goes something like this;

 1. Add new ```.md``` files to the ```./docs``` folder and index them in the ```./docs/pydoc-markdown.yml```
 2. Ensure that you have good doc strings in your DNA Workflow modules and then also add that module to the ```./docs/pydoc-markdown.yml```
 3. Run the ```pydoc-markdown``` script using the ```./docs/pydoc-markdown.yml```

```
pydoc-markdown docs/pydoc-markdown.yml
```

This will create a new ```./build``` directory which will be ignored by ```.gitignore``` but contains everything ```mkdocs``` needs to generate the new site.  We use the dedicated ```gh-pages``` branch to publish our documentation using this same repo.  ```mkdocs``` will autogenerate the site HTML and create/update this dedicated branch;

```
mkdocs gh-deploy -f build/docs/mkdocs.yml
```

For locall testing you can also use the ```-wo``` options to start a local web server to and browse the generated pages;

```
pydoc-markdown docs/pydoc-markdown.yml -wo
```

**WARNING:**

```pydoc-markdown``` does not copy the ./media files from ```./docs/media``` so it is necessary to also do this intermediate step also.  The full script should be (run from the project root dir);

```
pydoc-markdown docs/pydoc-markdown.yml
cp -r docs/media build/docs/docs/
mkdocs gh-deploy -f build/docs/mkdocs.yml
```

Or you can simply run the ```builddocs.sh``` script.
