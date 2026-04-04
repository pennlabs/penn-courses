import React, { Component } from "react";
import AsyncSelect from "react-select/lib/Async";
import { components } from "react-select";
import { withRouter } from "react-router-dom";
import styled from "styled-components";
import fuzzysort from "fuzzysort";
import { HiMagnifyingGlass } from "react-icons/hi2";
import { apiAutocomplete } from "../utils/api";

const SearchBarWrapper = styled.div`
  display: flex;
  height: 40px;
  width: 100%; 
  min-width: 0; 
  align-items: center;
  border-radius: 8px;
  align-self: stretch;
  border: 1px solid #ebeef2;
  background: #f7f9fb;
`;

const SearchInputStyled = styled.input`
  border: none;
  background: transparent;
  outline: none;
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0px 12px;
  color: #6d6f71;
  font-family: "SFPro", sans-serif;
  font-size: 14px;
  font-weight: 300;
  line-height: 150%;

  &:focus {
    background-color: transparent;
    outline: none;
  }
`;


function expandCombo(course) {
  const a = course.split(" ");
  return `${course} ${a[0]}-${a[1]} ${a[0]}${a[1]}`;
}

function removeDuplicates(dups) {
  const used = new Set();
  const clean = [];
  dups.forEach((i) => {
    if (!used.has(i.title)) {
      used.add(i.title);
      clean.push(i);
    }
  });
  return clean;
}

const CustomControl = ({ children, innerRef, innerProps }) => (
  <SearchBarWrapper ref={innerRef} {...innerProps}>
    <HiMagnifyingGlass
      style={{
        fontSize: "36px",
        paddingLeft: "12px",
        color: "#9ba0a5",
        flexShrink: 0,
      }}
    />
    {children}
  </SearchBarWrapper>
);

const CustomInput = (props) => {
  const { innerRef, isDisabled, isHidden, ...inputProps } = props;
  const {
    cx,
    getStyles,
    getValue,
    hasValue,
    selectProps,
    theme,
    isMulti,
    clearValue,
    ...domProps
  } = inputProps;
  if (isHidden) return <components.Input {...props} />;
  return (
    <SearchInputStyled
      ref={innerRef}
      disabled={isDisabled}
      placeholder="Search"
      {...domProps}
    />
  );
};

const NullComponent = () => null;

/**
 * The search bar that appears on the homepage and navigation bar.
 */
class SearchBar extends Component {
  constructor(props) {
    super(props);

    this.selectRef = React.createRef();

    this.state = {
      autocompleteOptions: [],
      searchValue: null,
    };

    this._autocompleteCallback = [];
    this.autocompleteCallback = this.autocompleteCallback.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.setFocusedOption = this.setFocusedOption.bind(this);
  }

  componentDidMount() {
    apiAutocomplete()
      .then((result) => {
        const courses = result.courses.map((i) => ({
          ...i,
          value: i.url,
          label: i.title,
          group: i.category,
          category: "Courses",
        }));
        const coursesIndex = [
          courses.map((i) => ({
            term: fuzzysort.prepare(expandCombo(i.title)),
            id: i.title,
          })),
        ];
        courses.forEach((i) => {
          coursesIndex.push(
            i.desc.map((j) => ({ term: fuzzysort.prepare(j), id: i.title }))
          );
        });

        const formattedAutocomplete = [
          {
            label: "Departments",
            options: result.departments.map((i) => ({
              ...i,
              value: i.url,
              label: i.title,
              group: i.category,
              search_desc: fuzzysort.prepare(i.desc),
              category: "Departments",
            })),
          },
          {
            label: "Courses",
            options: courses.reduce((map, obj) => {
              map[obj.title] = obj;
              return map;
            }, {}),
            search_index: coursesIndex.flat(),
          },
          {
            label: "Instructors",
            options: result.instructors.map((i) => ({
              ...i,
              value: i.url,
              label: i.title,
              group: i.category,
              search_desc: fuzzysort.prepare(i.desc),
              category: "Instructors",
            })),
          },
        ];

        this.setState({ autocompleteOptions: formattedAutocomplete }, () => {
          this._autocompleteCallback.forEach((x) =>
            x(this.state.autocompleteOptions)
          );
          this._autocompleteCallback = [];
        });
      })
      .catch((e) => {
        window.Raven.captureException(e);
        this.setState({ autocompleteOptions: [] }, () => {
          this._autocompleteCallback.forEach((x) =>
            x(this.state.autocompleteOptions)
          );
          this._autocompleteCallback = [];
        });
      });
  }

  filterOptionsList(autocompleteOptions, inputValue) {
    if (!inputValue) {
      return [
        {
          label: "Departments",
          options: autocompleteOptions[0].options.slice(0, 10),
        },
        {
          label: "Courses",
          options: Object.values(autocompleteOptions[1].options).slice(0, 25),
        },
        {
          label: "Instructors",
          options: autocompleteOptions[2].options.slice(0, 25),
        },
      ];
    }
    return fuzzysort
      .goAsync(inputValue, autocompleteOptions[1].search_index, {
        key: "term",
        threshold: -2000,
        limit: 25,
      })
      .then((res) => [
        {
          label: "Departments",
          options: fuzzysort
            .go(inputValue, autocompleteOptions[0].options, {
              keys: ["title", "search_desc"],
              threshold: -200,
              limit: 10,
            })
            .map(({ obj }) => obj),
        },
        {
          label: "Courses",
          options: removeDuplicates(
            res.map((a) => autocompleteOptions[1].options[a.obj.id])
          ),
        },
        {
          label: "Instructors",
          options: fuzzysort
            .go(inputValue, autocompleteOptions[2].options, {
              keys: ["title", "search_desc"],
              threshold: -200,
              limit: 25,
            })
            .map(({ obj }) => obj),
        },
      ]);
  }

  autocompleteCallback(inputValue) {
    this.setState({ searchValue: inputValue });
    return new Promise((resolve) => {
      if (this.state.autocompleteOptions.length) {
        resolve(this.state.autocompleteOptions);
      } else {
        this._autocompleteCallback.push(resolve);
      }
    })
      .then((res) => this.filterOptionsList(res, inputValue))
      .then((res) => {
        this.setFocusedOption();
        return res;
      });
  }

  setFocusedOption() {
    this.selectRef.current.select.select.getNextFocusedOption = (options) =>
      options[0];
  }

  handleChange(value) {
    this.props.history.push(value.url);
  }

  render() {
    const { state: parent } = this;
    return (
      <div id="search" style={{ minWidth: 0, width: "100%" }}>
        <AsyncSelect
          ref={this.selectRef}
          autoFocus={this.props.isTitle}
          onChange={this.handleChange}
          value={this.state.searchValue}
          placeholder=""
          loadOptions={this.autocompleteCallback}
          defaultOptions
          components={{
            Control: CustomControl,
            Input: CustomInput,
            DropdownIndicator: NullComponent,
            IndicatorSeparator: NullComponent,
            Placeholder: NullComponent,
            SingleValue: NullComponent,
            Option: (props) => {
              const { children, innerRef, innerProps, isFocused, data } = props;
              return (
                <div
                  ref={innerRef}
                  {...innerProps}
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: 6,
                    padding: "6px 14px",
                    cursor: "pointer",
                    fontFamily: "'SFPro', sans-serif",
                    background: isFocused ? "#f0f3f7" : "transparent",
                  }}
                >
                  <b
                    style={{
                      fontSize: 14,
                      fontWeight: 500,
                      color: "#1a1d21",
                    }}
                  >
                    {children}
                  </b>
                  <span style={{ color: "#aaa", fontSize: 12 }}>
                    {(() => {
                      const { desc } = data;
                      if (Array.isArray(desc)) {
                        const opt = fuzzysort
                          .go(parent.searchValue, desc, {
                            threshold: -Infinity,
                            limit: 1,
                          })
                          .map((a) => a.target);
                        return opt[0] || desc[0];
                      }
                      return desc;
                    })()}
                  </span>
                </div>
              );
            },
            GroupHeading: (props) => (
              <div
                style={{
                  padding: "8px 14px 4px",
                  fontFamily: "'SFPro', sans-serif",
                  fontSize: 11,
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  color: "#9ba0a5",
                }}
              >
                {props.children}
              </div>
            ),
          }}
          styles={{
            container: () => ({
              position: "relative",
            }),
            control: () => ({}),
            valueContainer: (base) => ({
              ...base,
              padding: 0,
              flex: 1,
              display: "flex",
              alignItems: "center",
              minWidth: 0,
            }),
            input: () => ({}),
            menu: (base) => ({
              ...base,
              borderRadius: 8,
              border: "1px solid #ebeef2",
              boxShadow: "0 4px 16px rgba(0, 0, 0, 0.08)",
              marginTop: 4,
              overflow: "hidden",
            }),
            menuList: (base) => ({
              ...base,
              padding: 0,
              maxHeight: 360,
            }),
            option: () => ({}),
            group: (base) => ({
              ...base,
              padding: 0,
            }),
            groupHeading: () => ({}),
            placeholder: () => ({ display: "none" }),
            indicatorsContainer: () => ({ display: "none" }),
          }}
        />
      </div>
    );
  }
}

export default withRouter(SearchBar);