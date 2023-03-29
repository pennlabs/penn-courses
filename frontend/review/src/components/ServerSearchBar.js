import React, { Component } from "react";
import AsyncSelect from "react-select/lib/Async";
import { components } from "react-select";
import { css } from "emotion";
import { withRouter } from "react-router-dom";
import fuzzysort from "fuzzysort";
import { apiSearch } from "../utils/api";
import { CoursePreview } from "./CoursePreview";
import { debounce } from 'lodash'

// Takes in a course (ex: CIS 160) and returns various formats (ex: CIS-160, CIS 160, CIS160).
function expandCombo(course) {
  const a = course.split(" ");
  return `${course} ${a[0]}-${a[1]} ${a[0]}${a[1]}`;
}

// Remove duplicate courses by topic.
function removeDuplicates(dups) {
  const used = new Set();
  const clean = [];
  dups.forEach(i => {
    if (!used.has(i.code)) {
      console.log(i)
      i.crosslistings.split(",").forEach(c => used.add(c));
      clean.push(i);
    }
  });
  return clean;
}

/**
 * The search bar that appears on the homepage and navigation bar.
 */
class ServerSearchBar extends Component {
  constructor(props) {
    super(props)
    this.selectRef = React.createRef();

    this.state = {
      autocompleteOptions: [],
      searchValue: null
    };

    this.autocompleteCallback = this.autocompleteCallback.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.setFocusedOption = this.setFocusedOption.bind(this);
    this.debouncedApiSearch = debounce(apiSearch, 250, { leading: true })
  }

  // Called each time the input value inside the searchbar changes
  autocompleteCallback(inputValue) {
    this.setState({ searchValue: inputValue });
    if (inputValue.length < 3) return [];
    return this.debouncedApiSearch(inputValue).then(courses => {
      const options = removeDuplicates(courses).map(course => ({
          ...course,
          url: `/course/${course.code.replace(' ', '-')}`,
      }));
      this.setState({ autocompleteOptions: options });
    })
  }

  // Hack to modify the handler to set the first option as the most relevant option
  setFocusedOption() {
    this.selectRef.current.select.select.getNextFocusedOption = options =>
      options[0];
  }

  // Called when an option is selected in the AsyncSelect component
  handleChange(value) {
    this.props.history.push(value.url);
  }

  render() {
    const { state: parent } = this;
    const width = this.props.isTitle
                ? "calc(100vw - 60px)"
                : "calc(100vw - 200px)";
    const maxWidth = this.props.isTitle ? 800 : 514;
    const coursePreviews = this.state.autocompleteOptions.map((course, index) => (
      <CoursePreview 
      key={index}
      onClick={() => {
        this.handleChange(course)
      }}
      course={course} 
      style={{ margin: "10px 0 0 0", backgroundColor: "#ffffff" }}
      />
    )) 

    return (
      <div 
      id="search"
      style={{ ...this.props.style }}
      >
        <div 
        style={{ 
          margin: "0 auto",
          height: this.props.isTitle ? 58 : 37
        }}
        >
          <AsyncSelect
            ref={this.selectRef}
            autoFocus={this.props.isTitle}
            onChange={this.handleChange}
            value={this.state.searchValue}
            placeholder={
              this.props.isTitle ? "Search for a class or professor" : ""
            }
            loadOptions={this.autocompleteCallback}
            defaultOptions
            components={{
              Option: props => {
                const {
                  children,
                  className,
                  cx,
                  getStyles,
                  isDisabled,
                  isFocused,
                  isSelected,
                  innerRef,
                  innerProps,
                  data
                } = props;
                return (
                  <div
                    ref={innerRef}
                    className={cx(
                      css(getStyles("option", props)),
                      {
                        option: true,
                        "option--is-disabled": isDisabled,
                        "option--is-focused": isFocused,
                        "option--is-selected": isSelected
                      },
                      className
                    )}
                    {...innerProps}
                  >
                    <b>{children}</b>
                    <span
                      style={{ color: "#aaa", fontSize: "0.8em", marginLeft: 3 }}
                    >
                      {(() => {
                        const { desc } = data;
                        if (Array.isArray(desc)) {
                          const opt = fuzzysort
                            .go(parent.searchValue, desc, {
                              threshold: -Infinity,
                              limit: 1
                            })
                            .map(a => a.target);
                          return opt[0] || desc[0];
                        }
                        return desc;
                      })()}
                    </span>
                  </div>
                );
              },
              DropdownIndicator: this.props.isTitle
                ? null
                : props => (
                    <components.DropdownIndicator {...props}>
                      <i className="fa fa-search mr-1" />
                    </components.DropdownIndicator>
                  )
            }}
            styles={{
              container: styles => ({
                ...styles,
                width: width,
                maxWidth: maxWidth,
              }),
              control: (styles, state) => ({
                ...styles,
                borderRadius: this.props.isTitle ? 0 : 32,
                boxShadow: !this.props.isTitle
                  ? "none"
                  : state.isFocused
                  ? "0px 2px 14px #ddd"
                  : "0 2px 14px 0 rgba(0, 0, 0, 0.07)",
                backgroundColor: this.props.isTitle ? "white" : "#f8f8f8",
                borderColor: "transparent",
                cursor: "pointer",
                "&:hover": {},
                fontSize: this.props.isTitle ? "30px" : null
              }),
              input: styles => ({
                ...styles,
                marginLeft: this.props.isTitle ? 0 : 10,
                outline: "none",
                border: "none"
              }),
              option: styles => ({
                ...styles,
                paddingTop: 5,
                paddingBottom: 5,
                cursor: "pointer"
              }),
              placeholder: styles => ({
                ...styles,
                whiteSpace: "nowrap",
                color: "#b2b2b2"
              }),
              menu: styles => ({
                ...styles,
                display: this.props.isTitle ? "none" : null
              })
            }}
          />
        </div>
        {this.props.isTitle &&
          <div
          style={{ width: width, maxWidth: maxWidth }}
          >
            {coursePreviews}
          </div>
          }
      </div>
    );
  }
}

export default withRouter(ServerSearchBar);
