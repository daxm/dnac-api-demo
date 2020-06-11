# DNA Workflows Demo 1

Open up the spreadsheet and enable only the Sites and IP Pools workflows.  Ensure that all functions are enabled under both of those workflows.

```
docker run -ti -v ${PWD}:/mnt dna_workflows:latest /bin/sh
```

Set all objects to 'present' and run with ```--noop```

```
python3 dna_workflows.py --noop
```

We see the functions that will be executed.

Note the **Stage** in the logging and functions staged for execution.


Execute the workbook for real:

```
python3 dna_workflows.py
```

 * Take a quick review of DNA Center UI

What happens if we rerun the script with same config?

```
python3 dna_workflows.py
```

As a development 'good practice' we test for existence before we try to create/delete anything:

```
python3 dna_workflows.py
```

Working with Excel is ok but sometimes we want to snapshot our current configuration data and store it version control.

For this, we can simply dump the entire Excel DB to YAML:

```
python3 dna_workflows.py --dump-db-to-yaml create-sites-ip-pools.yml --noop
```

No we update the Excel to mark all the objects as 'absent' and this time when we run, we'll also create the yaml dump.

```
python3 dna_workflows.py --dump-db-to-yaml delete-sites-ip-pools.yml
```

Let's take a quick look at the YAML file;

```
cat delete-sites-ip-pools.yml
```

Now we can store this file in Git and make incremental changes, use for regression testing etc.

We can also use this YAML file as the input to run ```dna_workflows.py```:

```
python3 dna_workflows.py --yaml-db create-sites-ip-pools.yml
python3 dna_workflows.py --yaml-db delete-sites-ip-pools.yml
```

Let's go back to the Excel and take a look at Task Scheduling.  See what happens if we try to make IP reservations before we create sites  Update the site.create() Stage to 3 and execute;

```
python3 dna_workflows.py
```

Reservations will now fail, but this expected.  Really we are just demonstrating the flexibility of the framework for custom script integration.

Finally, we can take a look at the [Usage Statistics](http://cx-emear-tools-stats.cisco.com/usage_statistics/)


# DNA Workflows Demo 2

Workflow manager helps users create new modules for DNA Workflows.  Using the workflow manager script we can create a skeleton module that will run the "Hello World" code from within the DNA Workflows framework;

Check out the help first;

```
python3 workflow_manager.py -h
```

Let's create a new module quickly.  Running the script below will;

 * Add a new module/worksheet to the Excel workbook
 * Create a new python module with basic "Hello World" code

```
python3 workflow_manager.py --add-workflow my_new_script_module
```

Open up the Excel and observe the new module and disable the other modules.  Now rerun the ```dna_workflows.py``` script;

```
python3 dna_workflows.py
```

Add some data to the new module in a table and rerun.

```
python3 dna_workflows.py
```

Finally, let's clean up that test module;

```
python3 workflow_manager.py --delete-workflow-and-clean my_new_script_module
```

# DNA Workflows Demo 3

Currently we have one example of a custom script submitted by Ivo Pinto in ./collections.

(requires Pandas)

```
cp -r collections/reports* ./
python3 dna_workflows.py --db reports.xlsx
```


