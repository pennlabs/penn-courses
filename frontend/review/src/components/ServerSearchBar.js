import React, { Component } from "react";
import AsyncSelect from "react-select/lib/Async";
import { components } from "react-select";
import { css } from "emotion";
import { withRouter } from "react-router-dom";
import fuzzysort from "fuzzysort";
import { apiSearch } from "../utils/api";
import { CoursePreview } from "./CoursePreview";
import { debounce } from 'lodash';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

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
    if (!used.has(i.topic)) {
      used.add(i.topic);
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
      searchValue: null,
      showFilters: false,
      difficulty: [0, 4],
      quality: [0, 4],
      work: [0, 4],
    };

    this.autocompleteCallback = this.autocompleteCallback.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.setFocusedOption = this.setFocusedOption.bind(this);
    this.debouncedApiSearch = debounce(apiSearch, 250, { leading: true })
  }

  // Called each time the input value inside the searchbar changes
  autocompleteCallback(inputValue) {
    this.setState({ searchValue: inputValue });
    if (inputValue.length < 3) return;
    return this.debouncedApiSearch(inputValue).then(courses => {
      const options = removeDuplicates(courses).map(course => ({
          ...course,
          url: `/course/${course.code}`,
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
    const coursePreviews = this.state.autocompleteOptions.map(course => (
      <CoursePreview 
      onClick={() => {
        console.log("hello")
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
          height: this.props.isTitle ? 58 : 37,
          display: "flex",
          flexDirection: "row",
          gap: "5"
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
          {this.props.isTitle &&
            <div id="filter-dropdown">
              <button 
              className="btn btn-sm btn-outline-primary"
              onClick={() => { this.setState({ showFilters: !this.state.showFilters }) }}
              style={{
                color: "#5a9093"
              }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-filter">
                  <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3">
                </polygon></svg>
              </button>
              <div
              style={{
                visibility: this.state.showFilters ? "visible" : "hidden",
                marginTop: "0.7rem",
                left: "0",
                paddingTop: "4px",
                position: "absolute",
                top: "100%",
                zIndex: 20,
                height: "200px",
                backgroundColor: "white",
                borderRadius: "4px",
                boxShadow: "0 2px 3px rgb(10 10 10 / 10%), 0 0 0 1px rgb(10 10 10 / 10%)",
                padding: "1rem",
                paddingRight: "1.25rem",
              }}
              >
                <div
                style={{
                  display: "flex",
                  flexDirection: "row",
                  gap: "15px",
                  height: "100%"
                }}
                >
                  <Slider
                  range
                  vertical
                  value={ this.state.quality }
                  onChange={ (e) => this.setState({ quality: e }) }
                  min={0}
                  max={4}
                  step={.1}
                  marks={{
                      0: { label: this.state.quality[0] },
                      4: { label: this.state.quality[1] },
                  }}
                  trackStyle={[{
                    backgroundColor: "#85b8ba"
                  }]}
                  handleStyle={[
                    { borderColor: "#85b8ba" },
                    { borderColor: "#85b8ba" },
                  ]}
                  />
                  <Slider
                  range
                  vertical
                  value={ this.state.difficulty }
                  onChange={ (e) => this.setState({ difficulty: e }) }
                  min={0}
                  max={4}
                  step={.1}
                  marks={{
                      0: { label: this.state.difficulty[0] },
                      4: { label: this.state.difficulty[1] },
                  }}
                  trackStyle={[{
                    backgroundColor: "#85b8ba"
                  }]}
                  handleStyle={[
                    { borderColor: "#85b8ba" },
                    { borderColor: "#85b8ba" },
                  ]}
                  />
                  <Slider
                  range
                  vertical
                  value={ this.state.work }
                  onChange={ (e) => this.setState({ work: e }) }
                  min={0}
                  max={4}
                  step={.1}
                  marks={{
                      0: { label: this.state.work[0] },
                      4: { label: this.state.work[1] },
                  }}
                  trackStyle={[{
                    backgroundColor: "#85b8ba"
                  }]}
                  handleStyle={[
                    { borderColor: "#85b8ba" },
                    { borderColor: "#85b8ba" },
                  ]}
                  />
                </div>
              </div>
            </div>
            }
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
