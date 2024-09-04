import os
import pickle
import networkx as nx
import matplotlib.pyplot as plt
from random_graph import delete_node,node_to_delete
import numpy as np

# Directory where graphs are stored
directory = '/home/morty/hypatia/ECE227/graph_72_22_53_550_starlinkshell1'

# List all pickle files in the directory
graph_files = [f for f in os.listdir(directory) if f.endswith('.pkl')]

# Load each graph
graphs = []
for filename in graph_files:
    filepath = os.path.join(directory, filename)
    with open(filepath, 'rb') as f:
        graph = pickle.load(f)
        graphs.append(graph)
    

filename = 'sat_usage.txt'
satellite_indices = []

with open(filename, 'r', encoding='utf-8') as file:
    lines = file.readlines()
    
    for line in lines:
        if len(satellite_indices)>=100:
            break
        parts = line.split()
        satellite_index = int(parts[3])  
        satellite_indices.append(satellite_index)
print(f'Satllite usage list read complete! top 10: {satellite_indices[:10]}')


# Define your ground stations and satellites
satellite_nodes = list(range(0, 1583))  # Satellite nodes IDs
ground_station_nodes = list(range(1583, 1684))  # Ground station node IDs
gs_num=len(ground_station_nodes)

hoop_list=np.zeros((len(graphs),int(gs_num*(gs_num-1)/2),2))

num_of_delete_node=10
remove_node_list=satellite_indices[:num_of_delete_node]


with open('inportant_node_delete(weighted).txt', 'w', encoding='utf-8') as file:
    header=f'top {num_of_delete_node} node deleted'
    file.write(header + '\n')
    for i in range(3): #range(len(graphs)):
        G=graphs[i]
        H=G.copy()
        H.remove_nodes_from([n for n in remove_node_list])
        k=0
        gs_list=ground_station_nodes.copy()
        for start_station in ground_station_nodes:
            if not gs_list:
                break 
            gs_list.pop(0)
            for end_station in gs_list:

                # Create a modified graph that excludes all ground stations except start and end
                F = G.copy()
                F.remove_nodes_from([n for n in ground_station_nodes if n not in [start_station, end_station]])
                # Compute the shortest path
            
                try:
                    path_length = nx.shortest_path_length(H, source=start_station, target=end_station, weight='weight')  # Use weight='weight' if your graph is weighted
                    hoop_list[i,k,0]=path_length
                    #print("Shortest path from A to E:", path)
                except nx.NetworkXNoPath:
                    hoop_list[i,k,0]=-1
                    #print("No path exists between the chosen nodes.")

                try:
                    path_r_length = nx.shortest_path_length(F, source=start_station, target=end_station, weight='weight')  # Use weight='weight' if your graph is weighted
                    hoop_list[i,k,1]=path_r_length
                    #print("Shortest path from A to E in random graph:", path_r)
                except nx.NetworkXNoPath:
                    hoop_list[i,k,1]=-1
                    #print("No path exists between the chosen nodes in random graph.")
                
                result=f'time: {i} ,start_gs: {start_station} ,end_gs: {end_station} ,before_delete: {hoop_list[i,k,0]} ,after_delte: {hoop_list[i,k,1]}'
                file.write(result +'\n')
                k=k+1
            print(f'time:{i}, start_node:{start_station}')
                

    '''                    
                try:
                    path = nx.shortest_path(H, source=start_station, target=end_station, weight='weight')  # Use weight='weight' if your graph is weighted
                    hoop_list[i,k,0]=len(path)
                    #print("Shortest path from A to E:", path)
                except nx.NetworkXNoPath:
                    hoop_list[i,k,0]=-1
                    #print("No path exists between the chosen nodes.")

                try:
                    path_r = nx.shortest_path(F, source=start_station, target=end_station, weight='weight')  # Use weight='weight' if your graph is weighted
                    hoop_list[i,k,1]=len(path_r)
                    #print("Shortest path from A to E in random graph:", path_r)
                except nx.NetworkXNoPath:
                    hoop_list[i,k,1]=-1
                    #print("No path exists between the chosen nodes in random graph.")
                k=k+1
                print(f'time:{i}, start_node:{start_node}, end_node:{end_node}')
        
        print('plot generating')
        plt.figure()
        nx.draw(G, with_labels=True,  node_size=10, font_size=5)
        plt.savefig(f'graph{i}.png')

        degree_dict = dict(H.degree())
        for node, degree in degree_dict.items():
            print(f"Node {node} has degree {degree}")
        '''
