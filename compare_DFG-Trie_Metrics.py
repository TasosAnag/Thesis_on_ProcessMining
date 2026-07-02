import pm4py

# ==========================================
# 1. Φόρτωση BPI Challenge 2017
# ==========================================
file_path = 'BPI_Challenge_2017.xes.gz' 
print("Ξεκινάει η φόρτωση του BPI 2017...")
log = pm4py.read_xes(file_path)

# Κρατάμε τις κορυφαίες 20 διαδρομές 
log_filtered = pm4py.filter_variants_top_k(log, 20)
print("Το Log φιλτραρίστηκε επιτυχώς στις κορυφαίες 20 διαδρομές.\n")

# ==========================================
# 2. Υπολογισμός Κόμβων/Ακμών για το DFG
# ==========================================
# Η συνάρτηση επιστρέφει το dfg (λεξικό με ακμές), start_activities και end_activities
dfg, start_activities, end_activities = pm4py.discover_dfg(log_filtered)

# Στο DFG, το πλήθος των ακμών είναι το μέγεθος του λεξικού
dfg_edges = len(dfg)

# Για τους κόμβους, μαζεύουμε όλες τις μοναδικές δραστηριότητες (source και target) από τις ακμές
dfg_nodes_set = set()
for source, target in dfg.keys():
    dfg_nodes_set.add(source)
    dfg_nodes_set.add(target)

# Προσθέτουμε για ασφάλεια και τις αρχικές/τελικές δραστηριότητες (συνήθως ήδη υπάρχουν)
for act in start_activities: dfg_nodes_set.add(act)
for act in end_activities: dfg_nodes_set.add(act)

dfg_nodes = len(dfg_nodes_set)

print("==========================================")
print("ΑΠΟΤΕΛΕΣΜΑΤΑ ΠΑΡΑΔΟΣΙΑΚΟΥ DFG")
print("==========================================")
print(f"-> Συνολικός Αριθμός Κόμβων : {dfg_nodes}")
print(f"-> Συνολικός Αριθμός Ακμών  : {dfg_edges}")


# ==========================================
# 3. Υπολογισμός Κόμβων/Ακμών για το Pure Trie
# ==========================================
def get_pure_trie_metrics(event_log):
    variants = pm4py.get_variants(event_log)
    
    trie = {}
    node_count = 1 # Ξεκινάμε με 1 για να συμπεριλάβουμε τη Ρίζα ('Start')
    
    for variant_key, traces_or_count in variants.items():
        activities = [act.strip() for act in variant_key.split(',')] if isinstance(variant_key, str) else variant_key
        
        current_node = trie
        for activity in activities:
            if activity not in current_node:
                # Κάθε φορά που δεν υπάρχει η δραστηριότητα, δημιουργούμε νέο κόμβο
                current_node[activity] = {'children': {}}
                node_count += 1 
            current_node = current_node[activity]['children']
            
    # Μαθηματικός κανόνας: Σε ένα αυστηρό δέντρο (χωρίς κύκλους ή συγχωνεύσεις), 
    # ο αριθμός των ακμών είναι ΠΑΝΤΑ ο αριθμός των κόμβων μείον 1.
    edge_count = node_count - 1 
    
    return node_count, edge_count

trie_nodes, trie_edges = get_pure_trie_metrics(log_filtered)

print("\n==========================================")
print("ΑΠΟΤΕΛΕΣΜΑΤΑ PURE PREFIX TREE (TRIE)")
print("==========================================")
print(f"-> Συνολικός Αριθμός Κόμβων : {trie_nodes}")
print(f"-> Συνολικός Αριθμός Ακμών  : {trie_edges}")
print("==========================================\n")
