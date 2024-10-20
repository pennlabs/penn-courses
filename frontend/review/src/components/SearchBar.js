import React, { Component } from "react";
import AsyncSelect from "react-select/lib/Async";
import { components } from "react-select";
import { css } from "emotion";
import { withRouter } from "react-router-dom";
import fuzzysort from "fuzzysort";
import { apiAutocomplete } from "../utils/api";

// Takes in a course (ex: CIS 160) and returns various formats (ex: CIS-160, CIS 160, CIS160).
function expandCombo(course) {
  const a = course.split(" ");
  return `${course} ${a[0]}-${a[1]} ${a[0]}${a[1]}`;
}

// Remove duplicate courses by title.
function removeDuplicates(dups) {
  const used = new Set();
  const clean = [];
  dups.forEach(i => {
    if (!used.has(i.title)) {
      used.add(i.title);
      clean.push(i);
    }
  });
  return clean;
}

/**
 * The search bar that appears on the homepage and navigation bar.
 */
class SearchBar extends Component {
  constructor(props) {
    super(props);

    this.selectRef = React.createRef();

    this.state = {
      autocompleteOptions: [],
      searchValue: null
    };

    this._autocompleteCallback = [];
    this.autocompleteCallback = this.autocompleteCallback.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.setFocusedOption = this.setFocusedOption.bind(this);
  }

  componentDidMount() {
    apiAutocomplete()
      .then(result => {
        const courses = result.courses.map(i => ({
          ...i,
          value: i.url,
          label: i.title,
          group: i.category,
          category: "Courses"
        }));
        const coursesIndex = [
          courses.map(i => ({
            term: fuzzysort.prepare(expandCombo(i.title)),
            id: i.title
          }))
        ];
        courses.forEach(i => {
          coursesIndex.push(
            i.desc.map(j => ({ term: fuzzysort.prepare(j), id: i.title }))
          );
        });

        const formattedAutocomplete = [
          {
            label: "Departments",
            options: result.departments.map(i => ({
              ...i,
              value: i.url,
              label: i.title,
              group: i.category,
              search_desc: fuzzysort.prepare(i.desc),
              category: "Departments"
            }))
          },
          {
            label: "Courses",
            options: courses.reduce((map, obj) => {
              map[obj.title] = obj;
              return map;
            }, {}),
            search_index: coursesIndex.flat()
          },
          {
            label: "Instructors",
            options: result.instructors.map(i => ({
              ...i,
              value: i.url,
              label: i.title,
              group: i.category,
              search_desc: fuzzysort.prepare(i.desc),
              category: "Instructors"
            }))
          }
        ];

        this.setState(
          {
            autocompleteOptions: formattedAutocomplete
          },
          () => {
            this._autocompleteCallback.forEach(x =>
              x(this.state.autocompleteOptions)
            );
            this._autocompleteCallback = [];
          }
        );
      })
      .catch(e => {
        window.Raven.captureException(e);
        this.setState(
          {
            autocompleteOptions: []
          },
          () => {
            this._autocompleteCallback.forEach(x =>
              x(this.state.autocompleteOptions)
            );
            this._autocompleteCallback = [];
          }
        );
      });
  }

  filterOptionsList(autocompleteOptions, inputValue) {
    if (!inputValue) {
      return [
        {
          label: "Departments",
          options: autocompleteOptions[0].options.slice(0, 10)
        },
        {
          label: "Courses",
          options: Object.values(autocompleteOptions[1].options).slice(0, 25)
        },
        {
          label: "Instructors",
          options: autocompleteOptions[2].options.slice(0, 25)
        }
      ];
    }
    return fuzzysort
      .goAsync(inputValue, autocompleteOptions[1].search_index, {
        key: "term",
        threshold: -2000,
        limit: 25
      })
      .then(res => [
        {
          label: "Departments",
          options: fuzzysort
            .go(inputValue, autocompleteOptions[0].options, {
              keys: ["title", "search_desc"],
              threshold: -200,
              limit: 10
            })
            .map(({ obj }) => obj)
        },
        {
          label: "Courses",
          options: removeDuplicates(
            res.map(a => autocompleteOptions[1].options[a.obj.id])
          )
        },
        {
          label: "Instructors",
          options: fuzzysort
            .go(inputValue, autocompleteOptions[2].options, {
              keys: ["title", "search_desc"],
              threshold: -200,
              limit: 25
            })
            .map(({ obj }) => obj)
        }
      ]);
  }

  // Called each time the input value inside the searchbar changes
  autocompleteCallback(inputValue) {
    this.setState({ searchValue: inputValue });
    return new Promise(resolve => {
      if (this.state.autocompleteOptions.length) {
        resolve(this.state.autocompleteOptions);
      } else {
        this._autocompleteCallback.push(resolve);
      }
    })
      .then(res => this.filterOptionsList(res, inputValue))
      .then(res => {
        this.setFocusedOption();
        return res;
      });
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
    return (
      <div id="search" style={{ margin: "0 auto" }}>
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
              width: this.props.isTitle
                ? "calc(100vw - 60px)"
                : "calc(100vw - 200px)",
              maxWidth: this.props.isTitle ? 600 : 514
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
            })
          }}
        />
      </div>
    );
  }
}

export default withRouter(SearchBar);
