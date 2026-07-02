import pm4py

import graphviz



# ==========================================

# 1. Φόρτωση BPI Challenge 2017

# ==========================================

file_path = 'BPI_Challenge_2017.xes.gz' 

print("Ξεκινάει η φόρτωση του BPI 2017...")

log = pm4py.read_xes(file_path)



# Κρατάμε τις κορυφαίες 20 διαδρομές 

log_filtered = pm4py.filter_variants_top_k(log, 20)

print("Το Log φιλτραρίστηκε επιτυχώς στις κορυφαίες 20 διαδρομές.")



# ==========================================

# 2. Κατασκευή Optimized Prefix Tree (Hybrid DAG)

# ==========================================

print("\nΔημιουργία Optimized Prefix Tree...")



def build_optimized_tree(event_log, min_support=5, merge_suffixes=True):

    variants = pm4py.get_variants(event_log)

    dot = graphviz.Digraph(comment='Optimized Tree', format='png')

    dot.attr(rankdir='LR')

    dot.node('root', 'Start', shape='doublecircle', style='filled', fillcolor='green')



    # 1. Κατασκευή του Trie στη μνήμη

    trie = {}

    for variant_key, traces_or_count in variants.items():

        # Διόρθωση για να διαβάζει σωστά το count ανάλογα με την έκδοση PM4Py

        count = len(traces_or_count) if isinstance(traces_or_count, list) else traces_or_count

        

        # --- PRUNING: Αγνοούμε πολύ σπάνιες διαδρομές (θόρυβος) ---

        if count < min_support:

            continue

            

        activities = [act.strip() for act in variant_key.split(',')] if isinstance(variant_key, str) else variant_key

        

        current_node = trie

        for activity in activities:

            if activity not in current_node:

                current_node[activity] = {'_count': 0, 'children': {}}

            current_node[activity]['_count'] += count

            current_node = current_node[activity]['children']



    # 2. Ζωγραφική με Σύμπτυξη (Merging)

    node_id_map = {} 

    node_counter = [0]

    edge_counter = [0] # Μετρητής για τις ακμές



    def draw_recursive(current_dict, parent_id, path_suffix):

        for act, data in current_dict.items():

            # Δημιουργούμε ένα κλειδί βασισμένο στη δραστηριότητα ΚΑΙ στο μέλλον της

            suffix_key = f"{act}_{str(list(data['children'].keys()))}" if merge_suffixes else f"{act}_{node_counter[0]}"

            

            if suffix_key not in node_id_map:

                current_id = f'n{node_counter[0]}'

                node_id_map[suffix_key] = current_id

                node_counter[0] += 1

                dot.node(current_id, act, fontsize='10')

            else:

                current_id = node_id_map[suffix_key]



            dot.edge(parent_id, current_id, label=str(data['_count']))

            edge_counter[0] += 1 # Αυξάνουμε τον μετρητή ακμών

            

            # Συνεχίζουμε αναδρομικά

            draw_recursive(data['children'], current_id, suffix_key)



    draw_recursive(trie, 'root', 'root')

    

    # Ο συνολικός αριθμός κόμβων είναι ο node_counter + 1 (για τον κόμβο 'Start')

    total_nodes = node_counter[0] + 1

    total_edges = edge_counter[0]

    

    return dot, total_nodes, total_edges



# ==========================================

# 3. Εκτέλεση και Εξαγωγή Αποτελεσμάτων

# ==========================================

# Τρέχουμε το πείραμα με min_support=10 για να κόψουμε τον θόρυβο

optimized_graph, num_nodes, num_edges = build_optimized_tree(log_filtered, min_support=10, merge_suffixes=True)

optimized_graph.render('bpi_optimized_hybrid_model', view=True)



print("\n==========================================")

print("ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΒΡΙΔΙΚΟΥ ΜΟΝΤΕΛΟΥ (SIMPLICITY)")

print("==========================================")

print(f"-> Συνολικός Αριθμός Κόμβων: {num_nodes}")

print(f"-> Συνολικός Αριθμός Ακμών: {num_edges}")

print("-> Το γράφημα αποθηκεύτηκε ως 'bpi_optimized_hybrid_model.png'")

print("==========================================")
