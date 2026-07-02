import pm4py
import pandas as pd
from sklearn.model_selection import KFold

def evaluate_models_generalization(log_path, k_splits=5):
    print(f"Φόρτωση Event Log: {log_path} ...")
    
    # 1. Φόρτωση του Event Log 
    log_df = pm4py.read_xes(log_path)
    
    print("Εξαγωγή των ιχνών (traces)...")
    # 2. Ομαδοποιούμε τα δεδομένα ανά Υπόθεση 
    # και φτιάχνουμε μια λίστα με τις δραστηριότητες  για κάθε ίχνος
    traces = log_df.groupby('case:concept:name', sort=False)['concept:name'].apply(list).tolist()
    
    print(f"Βρέθηκαν {len(traces)} συνολικά ίχνη.")
    
    # 3. Ρύθμιση του K-Fold Cross Validation
    kf = KFold(n_splits=k_splits, shuffle=True, random_state=42)
    
    trie_generalization_scores = []
    dfg_generalization_scores = []
    
    print(f"\nΕκτέλεση {k_splits}-Fold Cross Validation...\n")
    
    fold = 1
    for train_index, test_index in kf.split(traces):
        # Διαχωρισμός σε Train και Test sets
        train_traces = [traces[i] for i in train_index]
        test_traces = [traces[i] for i in test_index]
        
        # --- ΕΚΠΑΙΔΕΥΣΗ ΜΟΝΤΕΛΩΝ ΠΑΝΩ ΣΤΟ TRAIN SET ---
        
        # A. Κατασκευή Trie: Απομνημονεύει ακριβώς τα traces που έχει δει (ως tuples)
        train_trie_memory = set(tuple(t) for t in train_traces)
        
        # B. Κατασκευή DFG: Απομνημονεύει μόνο τις μεταβάσεις (Directly-Follows relations)
        train_dfg_edges = set()
        for t in train_traces:
            for i in range(len(t) - 1):
                train_dfg_edges.add((t[i], t[i+1]))
                
        # --- ΑΞΙΟΛΟΓΗΣΗ (TESTING) ΠΑΝΩ ΣΤΟ TEST SET ---
        trie_success = 0
        dfg_success = 0
        
        for t in test_traces:
            # Αξιολόγηση Trie: Το ίχνος επιτρέπεται ΜΟΝΟ αν το Trie το έχει ξαναδεί
            if tuple(t) in train_trie_memory:
                trie_success += 1
                
            # Αξιολόγηση DFG: Το ίχνος επιτρέπεται αν ΟΛΕΣ του οι μεταβάσεις υπάρχουν στο DFG
            is_dfg_valid = True
            for i in range(len(t) - 1):
                if (t[i], t[i+1]) not in train_dfg_edges:
                    is_dfg_valid = False
                    break
            
            if is_dfg_valid:
                dfg_success += 1
                
        # Υπολογισμός ποσοστών επιτυχίας (Fitness) για το τρέχον fold
        trie_score = trie_success / len(test_traces)
        dfg_score = dfg_success / len(test_traces)
        
        trie_generalization_scores.append(trie_score)
        dfg_generalization_scores.append(dfg_score)
        
        print(f"Fold {fold}:")
        print(f"  Trie Test Fitness: {trie_score:.2%}")
        print(f"  DFG  Test Fitness: {dfg_score:.2%}")
        fold += 1

    # 4. Τελικά Συμπεράσματα
    avg_trie = sum(trie_generalization_scores) / k_splits
    avg_dfg = sum(dfg_generalization_scores) / k_splits
    
    print("\n" + "="*30)
    print("=== ΤΕΛΙΚΑ ΑΠΟΤΕΛΕΣΜΑΤΑ ===")
    print("="*30)
    print(f"Μέσο Test Fitness DFG:  {avg_dfg:.2%}")
    print(f"Μέσο Test Fitness Trie: {avg_trie:.2%}")

if __name__ == '__main__':
  
    evaluate_models_generalization("BPI_Challenge_2017.xes.gz", k_splits=5)
