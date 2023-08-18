# nanonis-data-browser

## How to start the data browser in a jupyter notebook
```
import loadapp

app = loadapp(auto_start_up_bool=True,directory='./testdata/')

display(app.tab)
```
alternatively without the autostart:
```
import loadapp

app = loadapp()

display(app.tab)
```
