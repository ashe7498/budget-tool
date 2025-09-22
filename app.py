import streamlit as st
import pandas as pd

st.title("🏗️ Item Cost Estimator Per Area")

# Upload Area CSV
st.subheader("📂 Upload Area CSV File")
area_file = st.file_uploader("Choose Area CSV file", type=["csv"])

# Upload Category CSV
st.subheader("📂 Upload Category CSV File")
category_file = st.file_uploader("Choose Category CSV file", type=["csv"])

if area_file and category_file:
    area_df = pd.read_csv(area_file)
    category_df = pd.read_csv(category_file)

    # Validate columns
    if not all(col in area_df.columns for col in ['item_number', 'area_name', 'area_value']):
        st.error("❌ Area CSV must have columns: item_number, area_name, area_value")
    elif not all(col in category_df.columns for col in ['category_item_number', 'category', 'item', 'cost', 'cost_unit', 'density', 'density_unit']):
        st.error("❌ Category CSV must have columns: category_item_number, category, item, cost, cost_unit, density, density_unit")
    else:
        st.success("✅ Both CSV files uploaded and verified!")

        # Initialize session state
        if 'grand_totals' not in st.session_state:
            st.session_state.grand_totals = {}
        if 'completed_items' not in st.session_state:
            st.session_state.completed_items = {}
        if 'button_disabled' not in st.session_state:
            st.session_state.button_disabled = False
        if 'current_area' not in st.session_state:
            st.session_state.current_area = None
        if 'quantity_assumed' not in st.session_state:
            st.session_state.quantity_assumed = {}
        if 'total_costs' not in st.session_state:
            st.session_state.total_costs = {}
        if 'selected_item' not in st.session_state:
            st.session_state.selected_item = None
        if 'selected_category' not in st.session_state:
            st.session_state.selected_category = None

        st.subheader("1️⃣ Select Area")
        area_names = area_df['area_name'].unique()
        selected_area = st.selectbox("Select an area", area_names)

        # Reset state on area change
        if st.session_state.current_area != selected_area:
            st.session_state.current_area = selected_area
            st.session_state.button_disabled = False
            if selected_area not in st.session_state.grand_totals:
                st.session_state.grand_totals[selected_area] = 0.0
            if selected_area not in st.session_state.completed_items:
                st.session_state.completed_items[selected_area] = set()
            if selected_area not in st.session_state.quantity_assumed:
                st.session_state.quantity_assumed[selected_area] = {}
            if selected_area not in st.session_state.total_costs:
                st.session_state.total_costs[selected_area] = {}
            st.session_state.selected_item = None
            st.session_state.selected_category = None

        area_row = area_df[area_df['area_name'] == selected_area].iloc[0]
        area_sqft = area_row['area_value']
        st.write(f"📐 Area size: **{area_sqft} sqft**")

        st.subheader("2️⃣ Select Category")
        categories = category_df['category'].unique()
        selected_category = st.selectbox("Select a category", categories, index=0)
        st.session_state.selected_category = selected_category

        # Filter items based on category
        category_items = category_df[category_df['category'] == selected_category]['item'].unique()
        available_items = [i for i in category_items if i not in st.session_state.completed_items[selected_area]]

        st.subheader("3️⃣ Select Item")
        if not available_items:
            st.info("✅ All items in this category have been added for this area.")
        else:
            if st.session_state.selected_item not in available_items:
                st.session_state.selected_item = available_items[0]

            selected_item = st.selectbox("Select an item", available_items, index=available_items.index(st.session_state.selected_item))
            st.session_state.selected_item = selected_item

            item_row = category_df[(category_df['item'] == selected_item) & (category_df['category'] == selected_category)].iloc[0]
            cost_unit = item_row['cost_unit']
            cost_per_unit = item_row['cost']
            default_density = item_row['density']
            density_unit = item_row['density_unit']
            
            if cost_unit != density_unit:
                st.write(f"Item cost: **${cost_per_unit} per {cost_unit}**")
                st.write(f"Item density: **{default_density} {cost_unit} per {density_unit}**")
            else:
                st.write(f"Item cost: **{cost_per_unit} per {cost_unit}**")

            if density_unit == 'sqft':
                st.write(f"Using area sqft ({area_sqft}) by default.")
                total_quantity = st.number_input(
                    f"Optional: Override area",
                    min_value=0.0,
                    value=float(area_sqft)
                )
            else:
                total_quantity = st.number_input(f"Enter total {density_unit} needed", min_value=0.0, step=1.0)

            if cost_unit != density_unit:
                override_density = st.number_input(
                    f"Optional: Override density ({cost_unit} per {density_unit})",
                    min_value=0.0,
                    value=default_density
                )
            else:
                override_density = default_density

            quantity_assumed_val = st.text_input(
                "Assumptions",
                placeholder="Enter your assumptions here"
            )


            total_cost = None
            if total_quantity > 0 and override_density > 0:
                units_needed = total_quantity * override_density
                total_cost = units_needed * cost_per_unit

            elif total_quantity > 0 and override_density == 0:
                units_needed = total_quantity
                total_cost = units_needed * cost_per_unit

            if total_cost is not None:
                st.subheader("📊 Results")
                st.metric("Units Needed", f"{units_needed:,.2f} {cost_unit}")
                st.metric("Cost per Unit", f"${cost_per_unit:,.2f} per {cost_unit}")
                st.metric("Total Cost", f"${total_cost:,.2f}")

                def add_to_total():
                    st.session_state.grand_totals[selected_area] += total_cost
                    st.session_state.completed_items[selected_area].add(selected_item)
                    st.session_state.quantity_assumed[selected_area][selected_item] = quantity_assumed_val
                    st.session_state.total_costs[selected_area][selected_item] = total_cost
                    st.session_state.button_disabled = True

                    # Refresh available items
                    new_available = [i for i in category_df[category_df['category'] == selected_category]['item'].unique() if i not in st.session_state.completed_items[selected_area]]
                    if new_available:
                        st.session_state.selected_item = new_available[0]
                        st.session_state.button_disabled = False
                    else:
                        st.session_state.selected_item = None

                st.button(
                    "➕ Add to Grand Total",
                    on_click=add_to_total,
                    disabled=st.session_state.button_disabled
                )
            else:
                st.info("ℹ️ Please enter valid values to calculate.")

        # Show grand total
        grand_total = round(st.session_state.grand_totals.get(selected_area, 0.0), 2)
        if grand_total == -0.0:
            grand_total = 0.0
        st.markdown(f"### 💰 Grand Total for **{selected_area}**: ${grand_total:,.2f}")

        # Show completed items
        completed = list(st.session_state.completed_items.get(selected_area, set()))
        if completed:
            st.subheader("✅ Completed Items")
            for idx, item in enumerate(completed, start=1):
                quantity_assumed_display = st.session_state.quantity_assumed[selected_area].get(item, 0.0)
                total_cost_val = st.session_state.total_costs[selected_area].get(item, 0.0)

                cols = st.columns([0.5, 4, 2, 2, 1])
                cols[0].write(f"**{idx}**")
                cols[1].write(item)
                cols[2].write(quantity_assumed_display)
                cols[3].write(f"${total_cost_val:,.2f}")

                if cols[4].button("X", key=f"undo_{selected_area}_{item}"):
                    st.session_state.completed_items[selected_area].remove(item)
                    st.session_state.grand_totals[selected_area] -= total_cost_val
                    del st.session_state.quantity_assumed[selected_area][item]
                    del st.session_state.total_costs[selected_area][item]
                    st.session_state.button_disabled = False
                    st.session_state.selected_item = item

else:
    st.info("⏳ Please upload both Area CSV and Category CSV to continue.")