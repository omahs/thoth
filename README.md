# Thoth

Thoth (pronounced "toss") is a Cairo/Starknet disassembler written in Python 3. Thoth's features also include the generation of the call graph and control-flow graph of a given Cairo/Starknet compilation artifact.

## Installation

```sh
sudo apt install graphviz

git clone https://github.com/FuzzingLabs/thoth && cd thoth

pip install .

thoth -h
```

## Disassemble the contract's compilation artifact (json)


```sh
thoth -f tests/json_files/cairo_array_sum.json
```

To get a pretty colored version:

```sh
thoth -f tests/json_files/cairo_array_sum.json -color
```
<p align="center">
	<img src="/images/thoth_disas_color.png"/>
</p>

To get a verbose version with more details about decoded bytecodes:
```sh
thoth -f tests/json_files/cairo_array_sum.json -vvv
```

## Print the contract's call graph 

The call flow graph represents calling relationships between functions of the contract. We tried to provide a maximum of information, such as the entry-point functions, the imports, decorators, etc.

```sh
thoth -f tests/json_files/cairo_array_sum.json -call
```
The output file (pdf/svg/png) and the dot file are inside the `output-callgraph` folder.
If needed, you can also visualize dot files online using [this](https://dreampuf.github.io/GraphvizOnline/) side. An example of a more complexe callgraph is available [here](images/starknet_get_full_contract_l2_dai_bridge.gv.png).

<p align="center">
	<img src="/images/thoth_callgraph_simple.png"/>
</p>

Legend:
<p align="center">
	<img src="/images/callgraph_legend.png"/>
</p>

For a specific output format (pdf/svg/png):
```sh
thoth -f tests/json_files/cairo_array_sum.json -call -format png
```

## Print the contract's control-flow graph (CFG)

```sh
thoth -f tests/json_files/cairo_array_sum.json -cfg
```
The output file (pdf/svg/png) and the dot file are inside the `output-cfg` folder.

<p align="center">
	<img src="/images/cairo_array_sum.gv.png"/>
</p>

For a specific function:
```sh
thoth -f tests/json_files/cairo_array_sum.json -cfg -function "__main__.main"
```

For a specific output format (pdf/svg/png):
```sh
thoth -f tests/json_files/cairo_array_sum.json -cfg -format png
```

## How to find a Cairo/Starknet compilation artifact (json file)

Thoth support cairo and starknet compilation artifact (json file) generated after compilation using `cairo-compile` or `starknet-compile`. Thoth also support the json file returned by: `starknet get_full_contract`.

# License

Thoth is licensed and distributed under the AGPLv3 license. [Contact us](mailto:contact@fuzzinglabs.com) if you're looking for an exception to the terms.
