import wikipediaapi
import torch
import numpy as np
from sentence_transformers import CrossEncoder

# Setup the AI Brain
device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2', device=device)

# The Original Wikipedia Object
wiki = wikipediaapi.Wikipedia(
    user_agent='WikiSpeedrunnerOriginal/1.0 (contact: cheese@email.com)',
    language='en'
)

def get_shortest_path(start, target):
    # (score, path)
    queue = [(0, [start])]
    visited = {start}

    while queue:
        # Sort queue: Best (most negative) scores first
        queue.sort(key=lambda x: x[0])
        _, path = queue.pop(0)
        current = path[-1]

        print(f"🧐 AI is looking at: {current}")
        page = wiki.page(current)
        
        # 1. CLEANING & FILTERING
        all_links = []
        for l in page.links.keys():
            if ":" in l: continue
            # Anti-Loop: Skip disambiguation pages and tiny numbers/years
            if "disambiguation" in l.lower(): continue
            if l.isdigit() and len(l) < 3: continue 
            all_links.append(l)

        target_lower = target.lower()
        if any(l.lower() == target_lower for l in all_links):
            # Find the actual original casing to return a valid URL
            actual_title = next(l for l in all_links if l.lower() == target_lower)
            return path + [actual_title]

        # 2. SLIDING WINDOW (Broad Sampling)
        links_arr = np.array(all_links)
        
        if len(links_arr) == 0:
            continue

        if len(links_arr) < 600:
            candidates = links_arr
        else:
            # Fixed concatenate syntax: added [] brackets
            candidates = np.concatenate([
                links_arr[:200], 
                links_arr[len(links_arr)//2 : len(links_arr)//2 + 200], 
                links_arr[-200:]
            ])
            
        pairs = [[target, str(t)] for t in candidates]
        initial_scores = model.predict(pairs, batch_size=len(pairs), show_progress_bar=False)
        
        # 4. THE LOOKAHEAD (Depth Perception)
        # Identify top 5 links based on title alone
        top_indices = np.argsort(initial_scores)[::-1][:5]
        
        final_queue_items = []
        for i, title in enumerate(candidates):
            if title in visited: continue
            
            score = initial_scores[i]
            
            # Deep Peek for high-potential links
            if i in top_indices:
                peek_page = wiki.page(title)
                # Feed the AI the page summary to see if it's a "Highway"
                context_pair = [target, peek_page.summary[:500]]
                lookahead_score = model.predict([context_pair], show_progress_bar=False)[0]
                
                # Blend title score with summary score
                score = (score + lookahead_score) / 2
            
            visited.add(title)
            # Use negative score for the min-priority queue
            final_queue_items.append((-score, path + [title]))

        queue.extend(final_queue_items)
        
        # Keep the memory usage in check
        if len(queue) > 1000:
            queue = queue[:1000]
            
        # Global safety break
        if len(visited) > 4000:
            break

    return None