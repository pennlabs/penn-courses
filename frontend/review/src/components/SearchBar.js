import React, { Component } from "react";
import { withRouter } from "react-router-dom";
import styled from "styled-components";

/**
 * The search bar that appears on the homepage and navigation bar.
 */
const Search = styled.div`
  margin: 0 auto;
  height: 4rem;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .5rem;
  box-shadow: rgba(0, 0, 0, 0.07) 0px 2px 14px 0px;
  background-color: #ffffff;
  border-radius: 5px;
  width: calc(100vw - 60px);
  max-width: 600px;
  -webkit-box-align: center;
  flex: 1 1 0%;
  flex-wrap: wrap;
  padding: 2px 8px;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
`
const SearchInput = styled.input`
  height: 100%;
  width: 90%;
  border: none;
  flex: 1;
  font-size: 30px;
  color: rgb(178, 178, 178);
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  box-sizing: border-box;
  white-space: nowrap;
`

class SearchBar extends Component {
  constructor(props) {
    super(props);
    this.selectRef = React.createRef();
  }
  handleDeepSearch(event) {
    if (event.key.length === 1 && /\S/.test(event.key)) {
      this.props.history.push("/search", { query: event.key });
    }
  }

  render() {
    return (
      <Search>
        <SearchInput
          autoFocus={!!this.props.autoFocus}
          placeholder="Search for a class or professor"
          onKeyDown={(e => {this.handleDeepSearch(e)})}
        />
      </Search>
    )
  }
}

export default withRouter(SearchBar);

