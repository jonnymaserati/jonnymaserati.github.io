---
layout: post
title:  "Connection Conundrums - Part 2"
tags: python wells drilling casing connections engineering data
---
In [part 2]({% post_url 2021-03-14-connection-conundrums-part-2 %}) we took our imported catalogue data and used it to populate a network graph, linking casing connection *nodes/vertices* together with *edges* between casing connections that we're interested in running together.

In this post, we'll take a look at some functions for interrogating our network graph to provide us with casing design options.

## Getting Started
First let's import our libraries, including the script we wrote in the previous post (so make sure that the scripts from part 1 and part 2 are in your working directory).
```python
import networkx as nx
import create_casing_connections_graph # our code from part 2
```
We can now generate our graph object with the following line:
```python
graph = create_casing_connections_graph.main()
```
## Roots and leaves
So let's answer the original question from part 1. To do this, we're going to assume that we're interested in only using these Tenaris Wedge 521 connections and that our surface casing size is 18 5/8". We need a function that will identify all our *root* nodes/vertices (i.e. our 18 5/8" surface casing connections) and find all the paths to all the *leaf* nodes/vertices (which may be the completion tubing connection).

A bit of background on graphs: the *in_degree* is the number of *edges* that lead into a *node/vertex*, while the *out_degree* is the number of *edges* that lead out of a *node/vertex*. A *root* has no *edges* leading into it and a *leaf* has no *edges* leading out of it. Think of a tree, with a root, branches and leaves.

The simplest way to get our roots (there can be more than one) and leaves is to loop though our 