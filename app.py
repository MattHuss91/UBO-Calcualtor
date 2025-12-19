import streamlit as st
import pandas as pd
from collections import defaultdict
import graphviz
import io

st.set_page_config(page_title="UBO Calculator", layout="wide")
st.title("Ultimate Beneficial Owner Calculator")

# Session State dataframes
if "entities" not in st.session_state: 
  st.session_state.entities = pd.DataFrame(columns=["EntityID", "Name", "Type", "Layer"])

if "relationships" not in st.session_state: 
  st.session_state.relationships = pd.DataFrame(columns=["OwnerID", "OwnedID", "RelationshipType", "OwnershipPct"])

entities = st.session_state.entities 
relationships = st.session_state.relationships

# Utilities
def sanitize_id(name: str) -> str: 
  return "".join(ch.lower() for ch in name if ch.isalnum())[:15]

def build_adj(df: pd.DataFrame, rel_type: str = "Equity"): 
  adj = defaultdict(list) 
  for _, r in df[df["RelationshipType"] == rel_type].iterrows(): 
    adj[r["OwnerID"]].append((r["OwnedID"], float(r["OwnershipPct"])))
  return adj

def find_paths(source: str, target: str, adj: dict): 
  out = [] 
  stack = [(source, [source], 1.0)] 
  while stack: 
    node, path, product = stack.pop() 
    if node == target and len(path) > 1: 
      out.append((path, product)) 
      continue 
    for child, pct in adj.get(node, []):
      if child in path: 
        continue  
      stack.append((child, path + [child], product * pct)) 
  return out

def compute_all_ultimate_ownership(entities: pd.DataFrame, relationships: pd.DataFrame, target: str):
  """Calculate ultimate ownership of target for ALL entities (not just above threshold)"""
  adj = build_adj(relationships, rel_type="Equity") 
  all_entity_ids = set(entities['EntityID'])
  entity_names = entities.set_index("EntityID")["Name"].to_dict()
  entity_types = entities.set_index("EntityID")["Type"].to_dict()
  
  # Calculate for every entity
  ultimate_ownership = {}
  
  for entity_id in all_entity_ids:
    paths = find_paths(entity_id, target, adj)
    total_ownership = sum(prod for _, prod in paths)
    if total_ownership > 0:
      ultimate_ownership[entity_id] = {
        'EntityID': entity_id,
        'Name': entity_names.get(entity_id, entity_id),
        'Type': entity_types.get(entity_id, 'Unknown'),
        'UltimateOwnership': total_ownership
      }
  
  return ultimate_ownership

def compute_ubo(entities: pd.DataFrame, relationships: pd.DataFrame, target: str, threshold: float): 
  adj = build_adj(relationships, rel_type="Equity") 
  sources = sorted(set(relationships[relationships["RelationshipType"]=="Equity"]["OwnerID"])) 
  entity_names = entities.set_index("EntityID")["Name"].to_dict() 
  
  paths_records = [] 
  for src in sources: 
    paths = find_paths(src, target, adj) 
    for pth, prod in paths: 
      paths_records.append({ 
        "OwnerID": src, 
        "OwnerName": entity_names.get(src, src), 
        "PathIDs": " -> ".join(pth), 
        "PathNames": " -> ".join(entity_names.get(i, i) for i in pth), 
        "PathOwnershipPct": prod, 
        "FinalTarget": entity_names.get(target, target),
      }) 
  paths_df = pd.DataFrame(paths_records) 
  if paths_df.empty: 
    agg = pd.DataFrame(columns=["OwnerID","OwnerName","AggregatedOwnershipPct","UBO_Flag"])
    return agg, paths_df 

  agg = paths_df.groupby(["OwnerID","OwnerName"])['PathOwnershipPct'].sum().reset_index() 
  agg.rename(columns={"PathOwnershipPct":"AggregatedOwnershipPct"}, inplace=True) 
  agg['UBO_Flag'] = agg['AggregatedOwnershipPct'] >= threshold  
  agg.sort_values('AggregatedOwnershipPct', ascending=False, inplace=True) 

  paths_df.sort_values(['OwnerName','PathOwnershipPct'], ascending=[True, False], inplace=True) 
  return agg, paths_df

def ownership_sums_per_entity(relationships: pd.DataFrame): 
  df = relationships[relationships['RelationshipType']=="Equity"].copy()
  if df.empty:
    return pd.DataFrame(columns=['OwnedID', 'OwnershipPct'])
  df['OwnershipPct'] = df['OwnershipPct'].astype(float) 
  sums = df.groupby('OwnedID')['OwnershipPct'].sum().reset_index() 
  return sums

def get_relationship_status(owner_id: str, owned_id: str, relationships: pd.DataFrame):
  """Check if an entity is a shareholder, director, or both"""
  rels = relationships[(relationships['OwnerID'] == owner_id) & (relationships['OwnedID'] == owned_id)]
  
  has_equity = any(rels['RelationshipType'] == 'Equity')
  has_directorship = any(rels['RelationshipType'] == 'Directorship')
  
  if has_equity and has_directorship:
    return "both"
  elif has_equity:
    return "shareholder"
  elif has_directorship:
    return "director"
  return None

def make_dot(entities: pd.DataFrame, relationships: pd.DataFrame, target: str): 
  names = entities.set_index('EntityID')['Name'].to_dict() 
  types = entities.set_index('EntityID')['Type'].to_dict() 
  layers = entities.set_index('EntityID')['Layer'].to_dict() 
  
  # Calculate ultimate ownership
  ultimate_ownership = compute_all_ultimate_ownership(entities, relationships, target)

  # Node styling 
  company_style = 'shape=box, style=filled, color=white, fontcolor=white, fillcolor="#1f5f7a"' 
  person_style = 'shape=box, style=filled, color=white, fontcolor=white, fillcolor="#f28c28"' 

  dot_lines = ["digraph G {", "rankdir=TB", "splines=true", "fontname=Helvetica", "node [fontname=Helvetica, fontsize=10]", "edge [fontname=Helvetica, color=\"#2c3e50\", fontsize=9]"] 

  # Subgraphs to keep same ranks for each layer 
  max_layer = int(entities['Layer'].max()) if not entities.empty else 0 
  for L in range(0, max_layer+1): 
    dot_lines.append(f"subgraph cluster_layer_{L} {{ rank=same; color=\"#ffffff00\"; label=\"\";") 
    for eid, row in entities[entities['Layer']==L].set_index('EntityID').iterrows(): 
      style = company_style if row['Type'] == 'Company' else person_style 
      label = names.get(eid, eid)
      
      # Add type label
      type_label = "Company" if row['Type'] == 'Company' else "Person"
      
      # Add ultimate ownership to label if this entity owns the target
      if eid in ultimate_ownership and eid != target:
        ult_pct = ultimate_ownership[eid]['UltimateOwnership'] * 100
        label = f"{label}\\n[{type_label}]\\n({ult_pct:.2f}% of target)"
      else:
        label = f"{label}\\n[{type_label}]"
      
      dot_lines.append(f"\"{eid}\" [{style}, label=\"{label}\"];") 
    dot_lines.append("}") 

  # Process relationships - group by owner-owned pair
  relationship_pairs = {}
  for _, r in relationships.iterrows():
    key = (r['OwnerID'], r['OwnedID'])
    if key not in relationship_pairs:
      relationship_pairs[key] = {'equity': None, 'directorship': False}
    
    if r['RelationshipType'] == 'Equity':
      relationship_pairs[key]['equity'] = float(r['OwnershipPct'])
    else:
      relationship_pairs[key]['directorship'] = True

  # Edges with combined labels
  for (owner, owned), rels in relationship_pairs.items():
    labels = []
    
    if rels['equity'] is not None:
      pct = rels['equity'] * 100
      labels.append(f"{pct:.1f}% equity")
    
    if rels['directorship']:
      labels.append("director")
    
    label_text = " + ".join(labels)
    
    # Use solid line if any equity, dashed if only directorship
    if rels['equity'] is not None:
      dot_lines.append(f"\"{owner}\" -> \"{owned}\" [label=\"{label_text}\", arrowsize=0.8];")
    else:
      dot_lines.append(f"\"{owner}\" -> \"{owned}\" [style=dashed, arrowsize=0.6, color=\"#7f8c8d\", label=\"{label_text}\"];")
  
  dot_lines.append("}") 
  return "\n".join(dot_lines)

def render_diagram_to_png(dot_string: str):
  """Render DOT string to PNG bytes"""
  try:
    graph = graphviz.Source(dot_string)
    png_bytes = graph.pipe(format='png')
    return png_bytes
  except Exception as e:
    st.error(f"Error rendering diagram: {e}")
    return None

# Side Bar
st.sidebar.header("Settings") 
threshold = st.sidebar.slider("UBO threshold (%)", 5, 50, 25, step=1) / 100.0 

# Reset button
if st.sidebar.button("Reset All Data", type="primary"):
  st.session_state.entities = pd.DataFrame(columns=["EntityID", "Name", "Type", "Layer"])
  st.session_state.relationships = pd.DataFrame(columns=["OwnerID", "OwnedID", "RelationshipType", "OwnershipPct"])
  if "target_company" in st.session_state:
    del st.session_state.target_company
  st.rerun()

# Target company chooser 
company_options = list(entities[entities['Type']=='Company']['EntityID']) if not entities.empty else []
if "target_company" not in st.session_state: 
  st.session_state.target_company = company_options[0] if company_options else None 
if company_options:
  st.sidebar.selectbox("Target company (our business)", company_options, index=company_options.index(st.session_state.target_company) if st.session_state.target_company in company_options else 0, key="target_company")

# Layout columns: Inputs | Explanation | Diagram 
col1, col2, col3 = st.columns([1, 1, 1]) 

with col1: 
  st.subheader("Add / edit entities") 
  with st.form("add_entity", clear_on_submit=True): 
    name = st.text_input("Name") 
    typ = st.radio("Type", ["Company","Person"], horizontal=True) 
    layer = st.number_input("Layer (visual rank)", min_value=0, max_value=10, value=1) 
    submit = st.form_submit_button("Add entity") 
    if submit and name: 
      eid = sanitize_id(name) 
      if eid in set(entities['EntityID']): 
        st.warning("An entity with this derived ID already exists. Try another name.") 
      else: 
        new_row = pd.DataFrame([{"EntityID":eid, "Name":name, "Type":typ, "Layer":layer}])
        st.session_state.entities = pd.concat([entities, new_row], ignore_index=True)
        st.success(f"Added: {name}") 
        st.rerun()

  # Edit/Delete Entities
  if not entities.empty:
    st.divider()
    st.subheader("Edit or delete entities")
    entity_to_edit = st.selectbox("Select entity", entities['Name'].tolist(), key="entity_edit_select")
    
    if entity_to_edit:
      entity_row = entities[entities['Name'] == entity_to_edit].iloc[0]
      
      with st.form("edit_entity"):
        new_name = st.text_input("Name", value=entity_row['Name'])
        new_type = st.radio("Type", ["Company","Person"], index=0 if entity_row['Type']=='Company' else 1, horizontal=True)
        new_layer = st.number_input("Layer", min_value=0, max_value=10, value=int(entity_row['Layer']))
        
        col_update, col_delete = st.columns(2)
        with col_update:
          update_btn = st.form_submit_button("Update", type="primary")
        with col_delete:
          delete_btn = st.form_submit_button("Delete", type="secondary")
        
        if update_btn:
          idx = entities[entities['EntityID'] == entity_row['EntityID']].index[0]
          st.session_state.entities.at[idx, 'Name'] = new_name
          st.session_state.entities.at[idx, 'Type'] = new_type
          st.session_state.entities.at[idx, 'Layer'] = new_layer
          st.success(f"Updated: {new_name}")
          st.rerun()
        
        if delete_btn:
          # Remove entity
          st.session_state.entities = entities[entities['EntityID'] != entity_row['EntityID']].reset_index(drop=True)
          # Remove related relationships
          st.session_state.relationships = relationships[
            (relationships['OwnerID'] != entity_row['EntityID']) & 
            (relationships['OwnedID'] != entity_row['EntityID'])
          ].reset_index(drop=True)
          st.success(f"Deleted: {entity_row['Name']}")
          st.rerun()

  st.divider() 
  st.subheader("Add relationships") 
  owners = list(entities['EntityID']) if not entities.empty else []
  owneds = list(entities['EntityID']) if not entities.empty else []
  with st.form("add_rel", clear_on_submit=True): 
    reltype = st.radio("Relationship type", ["Equity","Directorship"], horizontal=True) 
    owner = st.selectbox("Owner", owners) if owners else st.selectbox("Owner", ["No entities yet"], disabled=True)
    owned = st.selectbox("Owned", owneds) if owneds else st.selectbox("Owned", ["No entities yet"], disabled=True)
    pct = st.number_input("Ownership % (if Equity)", min_value=0.0, max_value=100.0, value=25.0, step=1.0) 
    submit2 = st.form_submit_button("Add relationship") 
    if submit2 and owners and owneds: 
      new_row = pd.DataFrame([{"OwnerID":owner, "OwnedID":owned, "RelationshipType":reltype, "OwnershipPct":None if reltype!="Equity" else pct/100.0}])
      st.session_state.relationships = pd.concat([relationships, new_row], ignore_index=True)
      st.success("Relationship added") 
      st.rerun()

  # Edit/Delete Relationships
  if not relationships.empty:
    st.divider()
    st.subheader("Edit or delete relationships")
    
    # Create readable relationship labels
    rel_labels = []
    entity_names = entities.set_index('EntityID')['Name'].to_dict()
    for idx, row in relationships.iterrows():
      owner_name = entity_names.get(row['OwnerID'], row['OwnerID'])
      owned_name = entity_names.get(row['OwnedID'], row['OwnedID'])
      if row['RelationshipType'] == 'Equity':
        pct = f"{row['OwnershipPct']*100:.1f}%"
        rel_labels.append(f"{owner_name} → {owned_name} ({pct} equity)")
      else:
        rel_labels.append(f"{owner_name} → {owned_name} (Director)")
    
    rel_to_edit = st.selectbox("Select relationship", rel_labels, key="rel_edit_select")
    
    if rel_to_edit:
      rel_idx = rel_labels.index(rel_to_edit)
      rel_row = relationships.iloc[rel_idx]
      
      with st.form("edit_relationship"):
        new_reltype = st.radio("Type", ["Equity","Directorship"], 
                               index=0 if rel_row['RelationshipType']=='Equity' else 1, 
                               horizontal=True)
        new_owner = st.selectbox("Owner", list(entities['EntityID']), 
                                index=list(entities['EntityID']).index(rel_row['OwnerID']))
        new_owned = st.selectbox("Owned", list(entities['EntityID']), 
                                index=list(entities['EntityID']).index(rel_row['OwnedID']))
        new_pct = st.number_input("Ownership %", min_value=0.0, max_value=100.0, 
                                  value=float(rel_row['OwnershipPct']*100) if rel_row['OwnershipPct'] is not None else 25.0, 
                                  step=1.0)
        
        col_update, col_delete = st.columns(2)
        with col_update:
          update_rel_btn = st.form_submit_button("Update", type="primary")
        with col_delete:
          delete_rel_btn = st.form_submit_button("Delete", type="secondary")
        
        if update_rel_btn:
          st.session_state.relationships.at[rel_idx, 'OwnerID'] = new_owner
          st.session_state.relationships.at[rel_idx, 'OwnedID'] = new_owned
          st.session_state.relationships.at[rel_idx, 'RelationshipType'] = new_reltype
          st.session_state.relationships.at[rel_idx, 'OwnershipPct'] = None if new_reltype!="Equity" else new_pct/100.0
          st.success("Relationship updated")
          st.rerun()
        
        if delete_rel_btn:
          st.session_state.relationships = relationships.drop(rel_idx).reset_index(drop=True)
          st.success("Relationship deleted")
          st.rerun()
  
  st.divider() 
  st.subheader("Quick helper: equal-share directors") 
  company_list = list(entities[entities['Type']=='Company']['EntityID']) if not entities.empty else []
  with st.form("helper_equal", clear_on_submit=True): 
    company = st.selectbox("Company to own", company_list, key="eq_company") if company_list else st.selectbox("Company to own", ["No companies yet"], disabled=True, key="eq_company")
    prefix = st.text_input("Director name prefix", value="Director") 
    n = st.number_input("Number of directors", min_value=1, max_value=10, value=3) 
    add_dirs = st.form_submit_button("Create directors + equal equity")
    if add_dirs and company_list: 
      share = 1.0 / n 
      created = [] 
      for i in range(1, int(n)+1): 
        name_i = f"{prefix} {i}" 
        eid = sanitize_id(name_i)
        if eid not in set(entities['EntityID']): 
          new_entity = pd.DataFrame([{"EntityID":eid, "Name":name_i, "Type":"Person", "Layer":0}])
          st.session_state.entities = pd.concat([st.session_state.entities, new_entity], ignore_index=True)
        new_rel = pd.DataFrame([{"OwnerID":eid, "OwnedID":company, "RelationshipType":"Equity", "OwnershipPct":share}])
        st.session_state.relationships = pd.concat([st.session_state.relationships, new_rel], ignore_index=True)
        created.append(name_i) 
      st.success(f"Added: {', '.join(created)} with {round(share*100,2)}% each into {company}") 
      st.rerun()

with col2: 
  if st.session_state.target_company:
    st.subheader(f"Ultimate ownership of: {entities[entities['EntityID']==st.session_state.target_company]['Name'].values[0] if not entities.empty else 'Target'}")
    
    # Calculate ultimate ownership for all entities
    ultimate_ownership = compute_all_ultimate_ownership(entities, relationships, st.session_state.target_company)
    
    if ultimate_ownership:
      ult_df = pd.DataFrame(ultimate_ownership.values())
      ult_df = ult_df[ult_df['EntityID'] != st.session_state.target_company]  # Don't show target owning itself
      ult_df['Ownership %'] = (ult_df['UltimateOwnership'] * 100).round(2)
      ult_df = ult_df.sort_values('UltimateOwnership', ascending=False)
      
      # Add relationship status
      status_list = []
      for _, row in ult_df.iterrows():
        status = get_relationship_status(row['EntityID'], st.session_state.target_company, relationships)
        if status == "both":
          status_list.append("Shareholder & Director")
        elif status == "shareholder":
          status_list.append("Shareholder")
        elif status == "director":
          status_list.append("Director Only")
        else:
          status_list.append("Indirect Owner")
      
      ult_df['Status'] = status_list
      
      st.dataframe(
        ult_df[['Name', 'Type', 'Ownership %', 'Status']].rename(columns={'Name':'Entity', 'Ownership %':'Ultimate Ownership %'}),
        use_container_width=True,
        height=400
      )
    else:
      st.info("No ownership paths found to target.")
    
    st.divider()
    st.subheader("Detailed paths (for verification)")
    agg, paths = compute_ubo(entities, relationships, st.session_state.target_company, threshold) 
    if not paths.empty: 
      df_show = paths.copy() 
      df_show['Path %'] = (df_show['PathOwnershipPct']*100).round(2) 
      st.dataframe(df_show[['OwnerName','PathNames','Path %']].rename(columns={'OwnerName':'Owner','PathNames':'Path'}), use_container_width=True, height=250) 
    
    st.divider() 
    st.subheader(f"UBO flag (≥{threshold*100:.0f}% threshold)") 
    if not agg.empty: 
      show = agg.copy() 
      show['Aggregated %'] = (show['AggregatedOwnershipPct']*100).round(2) 
      st.dataframe(show[['OwnerName','Aggregated %','UBO_Flag']].rename(columns={'OwnerName':'Owner','UBO_Flag':'Is UBO'}), use_container_width=True, height=180) 
    else:
      st.info("No owners found.")
  else:
    st.info("Add a company entity to begin.")

  st.divider() 
  st.subheader("Validation: direct equity sums") 
  sums = ownership_sums_per_entity(relationships) 
  if len(sums):
    sums['Sum %'] = (sums['OwnershipPct']*100).round(2) 
    sums['Owned Name'] = sums['OwnedID'].map(entities.set_index('EntityID')['Name']) 
    st.dataframe(sums[['Owned Name','Sum %']].rename(columns={'Owned Name':'Entity'}), use_container_width=True, height=180) 
    warn_over = sums[sums['OwnershipPct']>1.0] 
    warn_under = sums[sums['OwnershipPct']<1.0] 
    if len(warn_over): 
      st.warning("Some entities have total equity > 100%. Check inputs.") 
    if len(warn_under): 
      st.info("Some entities have total equity < 100%. That is allowed but means unmodelled owners exist.") 
  else:
    st.info("No equity relationships yet.")

with col3: 
  st.subheader("Ownership diagram") 
  if not entities.empty and st.session_state.target_company:
    dot = make_dot(entities, relationships, st.session_state.target_company) 
    st.graphviz_chart(dot, use_container_width=True)
    
    # Download diagram as PNG
    png_data = render_diagram_to_png(dot)
    if png_data:
      st.download_button(
        label="Download Diagram (PNG)",
        data=png_data,
        file_name="ownership_diagram.png",
        mime="image/png"
      )
  elif not entities.empty:
    st.info("Select a target company to show ultimate ownership.")
  else:
    st.info("No entities to display.")

# Download
st.divider() 
colA, colB, colC, colD = st.columns(4) 
with colA: 
  if not entities.empty:
    st.download_button("Download Entities (CSV)", data=entities.to_csv(index=False), file_name="entities.csv", mime="text/csv") 
with colB: 
  if not relationships.empty:
    st.download_button("Download Relationships (CSV)", data=relationships.to_csv(index=False), file_name="relationships.csv", mime="text/csv") 
with colC: 
  if st.session_state.target_company:
    ultimate_ownership = compute_all_ultimate_ownership(entities, relationships, st.session_state.target_company)
    if ultimate_ownership:
      ult_df = pd.DataFrame(ultimate_ownership.values())
      ult_df = ult_df[ult_df['EntityID'] != st.session_state.target_company]
      st.download_button("Download Ultimate Ownership (CSV)", data=ult_df.to_csv(index=False), file_name="ultimate_ownership.csv", mime="text/csv")
with colD: 
  if st.session_state.target_company and 'paths' in locals() and not paths.empty:
    st.download_button("Download All Paths (CSV)", data=paths.to_csv(index=False), file_name="ownership_paths.csv", mime="text/csv") 

st.caption("Tip: For directors with equal shares, use the helper to generate people and equity links in one step.")
