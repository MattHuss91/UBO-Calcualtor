import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="UBO Calculator", layout="wide")
st.title("UBO Calculator")

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

def make_dot(entities: pd.DataFrame, relationships: pd.DataFrame): 
  names = entities.set_index('EntityID')['Name'].to_dict() 
  types = entities.set_index('EntityID')['Type'].to_dict() 
  layers = entities.set_index('EntityID')['Layer'].to_dict() 

  # Node styling 
  company_style = 'shape=box, style=filled, color=white, fontcolor=white, fillcolor="#1f5f7a"' 
  person_style = 'shape=box, style=filled, color=white, fontcolor=white, fillcolor="#f28c28"' 

  dot_lines = ["digraph G {", "rankdir=TB", "splines=true", "fontname=Helvetica", "node [fontname=Helvetica]", "edge [fontname=Helvetica, color=\"#2c3e50\"]"] 

  # Subgraphs to keep same ranks for each layer 
  max_layer = int(entities['Layer'].max()) if not entities.empty else 0 
  for L in range(0, max_layer+1): 
    dot_lines.append(f"subgraph cluster_layer_{L} {{ rank=same; color=\"#ffffff00\"; label=\"\";") 
    for eid, row in entities[entities['Layer']==L].set_index('EntityID').iterrows(): 
      style = company_style if row['Type'] == 'Company' else person_style 
      label = names.get(eid, eid)
      dot_lines.append(f"\"{eid}\" [{style}, label=\"{label}\"];") 
    dot_lines.append("}") 

  # Edges with labels
  for _, r in relationships.iterrows(): 
    owner, owned, reltype = r['OwnerID'], r['OwnedID'], r['RelationshipType'] 
    if reltype == 'Equity': 
      pct = int(round(float(r['OwnershipPct'])*100)) 
      dot_lines.append(f"\"{owner}\" -> \"{owned}\" [label=\"{pct}%\", arrowsize=0.8];") 
    else:  # Directorship 
      dot_lines.append(f"\"{owner}\" -> \"{owned}\" [style=dashed, arrowsize=0.6, color=\"#7f8c8d\", label=\"director\"];") 
  dot_lines.append("}") 
  return "\n".join(dot_lines)

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
  st.sidebar.selectbox("Target company (final owned entity)", company_options, index=company_options.index(st.session_state.target_company) if st.session_state.target_company in company_options else 0, key="target_company")

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
  st.subheader("Ownership explained (all paths → product of %s)") 
  if st.session_state.target_company:
    agg, paths = compute_ubo(entities, relationships, st.session_state.target_company, threshold) 
    if paths.empty: 
      st.info("No equity paths found to the target.") 
    else: 
      df_show = paths.copy() 
      df_show['Path %'] = (df_show['PathOwnershipPct']*100).round(2) 
      st.dataframe(df_show[['OwnerName','PathNames','Path %']].rename(columns={'OwnerName':'Owner','PathNames':'Path'}), use_container_width=True, height=330) 

    st.divider() 
    st.subheader("Aggregated ownership & UBO flag") 
    if agg.empty: 
      st.info("No owners found.") 
    else: 
      show = agg.copy() 
      show['Aggregated %'] = (show['AggregatedOwnershipPct']*100).round(2) 
      st.dataframe(show[['OwnerName','Aggregated %','UBO_Flag']].rename(columns={'OwnerName':'Owner','UBO_Flag':'UBO ≥ threshold'}), use_container_width=True, height=220) 
  else:
    st.info("Add a company entity to begin.")

  st.divider() 
  st.subheader("Validation: sum of equity into each owned entity") 
  sums = ownership_sums_per_entity(relationships) 
  if len(sums):
    sums['Sum %'] = (sums['OwnershipPct']*100).round(2) 
    sums['Owned Name'] = sums['OwnedID'].map(entities.set_index('EntityID')['Name']) 
    st.dataframe(sums[['Owned Name','Sum %']].rename(columns={'Owned Name':'Owned'}), use_container_width=True, height=180) 
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
  if not entities.empty:
    dot = make_dot(entities, relationships) 
    st.graphviz_chart(dot, use_container_width=True)
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
  if st.session_state.target_company and 'agg' in locals() and not agg.empty:
    st.download_button("Download UBO Summary (CSV)", data=agg.to_csv(index=False), file_name="ubo_summary.csv", mime="text/csv") 
with colD: 
  if st.session_state.target_company and 'paths' in locals() and not paths.empty:
    st.download_button("Download Paths (CSV)", data=paths.to_csv(index=False), file_name="ubo_paths.csv", mime="text/csv") 

st.caption("Tip: For directors with equal shares, use the helper to generate people and equity links in one step.")
