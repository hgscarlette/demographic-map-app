import streamlit as st
import pandas as pd

class DynamicFilters:
    """
    A class to create dynamic multi-select filters in Streamlit.
    
    Methods
    -------
    check_state():
        Initializes the session state with filters if not already set.
    filter_df(except_filter=None):
        Returns the dataframe filtered based on session state excluding the specified filter.
    display():
        Renders the dynamic filters and the filtered dataframe in Streamlit.
    """

    def __init__(self, df, filters):
        self.df = df
        self.filters = {filter_name: [] for filter_name in filters}
        self.check_state()

    def check_state(self):
        if "filters" not in st.session_state:
            st.session_state["filters"] = self.filters
            
    def reset_filters(self):
        """
        Can use a button:        
            st.button("Reset Filters", on_click=dynamic_filters.reset_filters)
        """
        if "filters" in st.session_state:
            del st.session_state["filters"]

    def filter_df(self, except_filter=None):
        """
        Filters the dataframe based on selected filtered stored in session states, except the vieweing filter (key).
        """
        filtered_df = self.df.copy()
        for key, values in st.session_state["filters"].items():
            if key != except_filter and values:
                filtered_df = filtered_df[filtered_df[key].isin(values)]
        return filtered_df

    def display_filters(self, num_cols):
        """
            Renders dynamic multiselect filters for user selection.

            Parameters:
            -----------
            location : str, optional
                The location where the filters are to be displayed. Accepted values are:
                - 'sidebar': Displays filters in the side panel of the application.
                - 'columns': Displays filters in columns format in the main application area.
                - None: Defaults to main application area without columns.
                Default is None.

            num_columns : int, optional
                The number of columns in which filters are to be displayed when location is set to 'columns'.
                Constraints:
                - Must be an integer.
                - Must be less than or equal to 8.
                - Must be less than or equal to the number of filters + 1.
                If location is 'columns', this value must be greater than 0.
                Default is 0.

            gap : str, optional
                Specifies the gap between columns when location is set to 'columns'. Accepted values are:
                - 'small': Minimal gap between columns.
                - 'medium': Moderate gap between columns.
                - 'large': Maximum gap between columns.
                Default is 'small'.

            Behavior:
            ---------
            - The function iterates through session-state filters.
            - For each filter, the function:
                1. Generates available filter options based on the current dataset.
                2. Displays a multiselect box for the user to make selections.
                3. Updates the session state with the user's selection.
            - If any filter value changes, the application triggers an update to adjust other filter options based on the current selection.
            - If a user's previous selection is no longer valid based on the dataset, it's removed.
            - If any filters are updated, the application will rerun for the changes to take effect.

            Exceptions:
            -----------
            Raises StreamlitAPIException if the provided arguments don't meet the required constraints.

            Notes:
            ------
            The function uses Streamlit's session state to maintain user's selections across reruns.
            """

        filters_changed = False
        col = 0
        col_list = st.columns(num_cols, gap="medium")

        for filter_name in st.session_state["filters"].keys():
            filtered_df = self.filter_df(filter_name)
            options = filtered_df[filter_name].unique().tolist()

            # Remove selected values that are not in options anymore
            valid_selections = [v for v in st.session_state["filters"][filter_name] if v in options]
            if valid_selections != st.session_state["filters"][filter_name]:
                st.session_state["filters"][filter_name] = valid_selections
                filters_changed = True
            
            # Show multi-select boxes on page
            with col_list[col]:
                selected = st.multiselect(f"Select {filter_name}", sorted(options),
                                        default=st.session_state["filters"][filter_name],
                                        key="filters" + filter_name)
            col += 1
            col = col % num_cols

            if selected != st.session_state["filters"][filter_name]:
                st.session_state["filters"][filter_name] = selected
                filters_changed = True

        if filters_changed:
            st.rerun()

    def display_df(self, **kwargs):
        """Renders the filtered dataframe in the main area."""
        # Display filtered DataFrame
        st.dataframe(self.filter_df(), **kwargs)
        return 