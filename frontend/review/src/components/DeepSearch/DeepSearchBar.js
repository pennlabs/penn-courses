import React, { Component } from "react";
import AsyncSelect from "react-select/lib/Async";
import { components } from "react-select";
import { withRouter } from "react-router-dom";
import fuzzysort from "fuzzysort";
import { apiSearch } from "../../utils/api";
import { CoursePreview } from "./CoursePreview";
import { debounce } from 'lodash';
import { Range } from 'rc-slider';
import 'rc-slider/assets/index.css';
import styled, { css } from "styled-components";
import { RatingBox } from "./RatingBox";
import { CodeDecoration } from "./CommonStyles";

const PCAGreen = (opacity = 1) => `rgba(90, 144, 147, ${opacity})`;

const FlexRow = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
`

const ConstWidthText = styled.div`
  width: 100px;
`

const Wrapper = styled.div`
  max-width: 768px;
  width: "100%";
  &:hover {
    cursor: pointer;
  }
`

const SearchWrapper = styled.div` // wrapper for searchbar + results
  width: 100%;
  display: flex;
  justify-content: center;
  flex-direction: column;
  gap: 5;
`

const Search = styled.div`
  margin: 0 auto;
  width: 100%;
  height: 4rem;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .5rem;
  box-shadow: 0 0 40px -12px rgb(0 0 0 / 0.25);
  padding: 1rem;
  background-color: #ffffff;
  border-radius: 5px;
`

const SliderDropDown = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 50%;
  margin-top: 1.5rem;
  right: -1rem;
  position: absolute;
  top: 100%;
  z-index: 20;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 3px rgb(10 10 10 / 10%), 0 0 0 1px rgb(10 10 10 / 10%);
  padding: 1rem;
  padding-right: 1.25rem;
  padding-bottom: 1.6rem;
  width: 20rem;
  box-shadow: 0 0 25px 0 rgb(0 0 0 / 10%);
`

const SearchInput = styled.input`
  height: 100%;
  border: none;
  flex: 1;
  border-bottom: 2px solid ${PCAGreen(.25)};
  &:focus {
    outline: none;
    border-bottom: 2px solid ${PCAGreen(.75)};
  }
  ::placeholder,
  ::-webkit-input-placeholder {
    font-style: italic;
  }
`

const PreviewWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: white;
  padding: 1rem;
  box-shadow: 0 0 22px -12px rgb(0 0 0 / 0.25);
  margin-bottom: 2rem;
  border-radius: 5px;
  & > div + div {
    border-top: 2px solid rgba(0, 0, 0, .25);
    padding-top: 1.5rem;
  }
`

const ResultCategory = styled.div` // Courses, Departments, Instructors
  margin-top: 1.5rem;
  margin-bottom: .75rem;
  width: 100%;
  color: #aaa;
  font-size: 14px;
  font-weight: bold;
  letter-spacing: -.25px;
  border-bottom: 1px solid #aaa;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
`

const InstructorPreviewComponent = ({ instructor: { name, departments, quality, work, difficulty }, onClick, history }) => (
  <FlexRow
  onClick={onClick}
  style={{
    fontSize: "1.25rem",
    justifyContent: "space-between",
    marginBottom: "1.5rem",
  }}
  >
    <div>
      <CodeDecoration
      style={{
        backgroundColor: "#e8f4ea",
      }}
      dangerouslySetInnerHTML={{ __html: name }}
      >
      </CodeDecoration>
      {" "}
      <span style={{
        opacity: .75,
        
      }}
      dangerouslySetInnerHTML={{ __html: departments?.join(", ") }}
      >
      </span>
    </div>
    <FlexRow>
      <RatingBox
      rating={quality}
      label="Quality"
      />
      <RatingBox
      rating={work}
      label="Work"
      />
      <RatingBox
      rating={difficulty}
      label="Difficulty"
      />
    </FlexRow>
  </FlexRow>
)

const DepartmentPreviewComponent = ({ department: { code, name, quality, work, difficulty }, onClick }) => (
  <FlexRow
  style={{
    fontSize: "1.25rem",
    justifyContent: "space-between",
    marginBottom: "1.5rem",
  }}
  onClick={onClick}
  >
    <div>
      <CodeDecoration
      style={{
        backgroundColor: "lavender",
      }}
      dangerouslySetInnerHTML={{ __html: code }}
      >
      </CodeDecoration>
      {" "}
      <span
      dangerouslySetInnerHTML={{ __html: name }}
      >
      </span>
    </div>
  </FlexRow>
)

const ResultCategoryComponent = ({ category, isFolded, setIsFolded }) => (
  <ResultCategory onClick={() => setIsFolded(!isFolded)}>
    <span>{category}</span>
    <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 512 512"
    style={{
      height: "1rem",
    }}
    >
      <path fill="none" stroke="currentColor" strokeLinecap="square" strokeMiterlimit="10" strokeWidth="48" 
      d={isFolded ? "MM112 328l144-144 144 144" : "M112 184l144 144 144-144"}
      key={isFolded}
      />
    </svg>
  </ResultCategory>
);

/**
 * The search bar that appears on the homepage and navigation bar.
 */
class DeepSearchBar extends Component {
  constructor(props) {
    super(props)
    this.selectRef = React.createRef();
    this.state = {
      isFirstRender: true,
      courseOptions: [],
      instructorOptions: [],
      departmentOptions: [],
      searchValue: props.initialSearchValue || null,
      showFilters: false,
      coursesFolded: false,
      departmentsFolded: false,
      instructorsFolded: false,
      difficulty: [0, 4],
      quality: [0, 4],
      work: [0, 4],
    };
    this.autocompleteCallback = this.autocompleteCallback.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.setFocusedOption = this.setFocusedOption.bind(this);
    this.debouncedApiSearch = debounce(apiSearch, 50, { leading: true })
  }

  componentDidMount() {
    if (this.props.state !== null) {
      const query = this.props.location.state.query;
      if (query !== '') {
        this.autocompleteCallback(query);
      }
    }
  }

  // Called each time the input value inside the searchbar changes
  autocompleteCallback(inputValue) {
    this.setState({ searchValue: inputValue });
    return this.debouncedApiSearch(inputValue, {
      workLow: this.state.work[0], workHigh: this.state.work[1],
      difficultyLow: this.state.difficulty[0], difficultyHigh: this.state.difficulty[1],
      qualityLow: this.state.quality[0], qualityHigh: this.state.quality[1]
    }).then((input) => {
      console.log(input);
      const departments = input["Departments"];
      const courses = input["Courses"];
      const instructors = input["Instructors"];

      const departments_input = departments.map((department) => {
        return {
          code: department.code,
          name: department.name,
        }
      })
      this.setState({ departmentOptions: departments_input });

      const courses_input = courses.map((course) => {
        return {
          code: course.code,
          title: course.title,
          description: course.description,
          quality: parseFloat(course.quality),
          work: parseFloat(course.work),
          difficulty: parseFloat(course.difficulty),
          current: course.current,
          instructors: course.instructors,
          cleanCode: course.cleanCode
        }
      })
      this.setState({ courseOptions: courses_input });

      const instructors_input = instructors.map((instructor) => {
        return {
          name: instructor.name,
          desc: instructor.desc,
          id: instructor.id
        }
      })
      this.setState({ instructorOptions: instructors_input });
    })
  }

  // Hack to modify the handler to set the first option as the most relevant option
  setFocusedOption() {
    this.selectRef.current.select.select.getNextFocusedOption = options =>
      options[0];
  }

  // Called when an option is selected in the AsyncSelect component
  handleChange(value) {
    this.props.history.push(value)
  }

  render() {
    const showCategoryHeaders =  [
      this.state.courseOptions.length,
      this.state.instructorOptions.length,
      this.state.departmentOptions.length
    ].filter(x => x > 0).length > 0;

    const coursePreviews = this.state.courseOptions.map((course, idx) => (
      <CoursePreview 
      key={idx}
      onClick={() => {
        this.handleChange(`/course/${course.cleanCode}`) // TODO: is this right?
      }}
      course={course} 
      />
    ))

    const instructorPreviews = this.state.instructorOptions.map((instructor, idx) => (
      <InstructorPreviewComponent
      key={idx}
      instructor={instructor}
      onClick={() => {
        this.handleChange(`/instructor/${instructor.id}`)
      }}
      />
    ))

    const departmentPreviews = this.state.departmentOptions.map((department, idx) => (
      <DepartmentPreviewComponent
      key={idx}
      onClick={() => {
        this.handleChange(`/department/${department.code}`) // TODO: is this right?
      }}
      department={department}
      />
    ))

    return (
      <Wrapper
      style={this.props.style}
      >
        <SearchWrapper>
          <Search>
            <img 
            src="/static/image/logo.png" 
            alt="Penn Course Review" 
            style={{
              height: "100%",
            }}
            onClick={() => {this.props.history.push("/")}}
            />{" "}
            <SearchInput 
            placeholder="Search for anything..."
            value={this.state.searchValue}
            onChange={(e) => {
              if (!this.state.isFirstRender) {
                this.autocompleteCallback(e.target.value);
              } else {
                this.setState({ isFirstRender: false });
              }
            }}
            autoFocus
            />
            <div 
            id="filter-dropdown"
            style={{
              position: "relative"
            }}
            >
              <button
              className="btn btn-sm btn-outline-primary"
              onClick={() => { this.setState({ showFilters: !this.state.showFilters }) }}
              style={{
                color: PCAGreen(.5),
              }}
              >
                <svg
                xmlns="http://www.w3.org/2000/svg"
                style={{
                  height: "1.5rem",
                  width: "1.5rem",
                }} 
                viewBox="0 0 512 512"
                stroke="currentColor" 
                fill="currentColor"
                >
                  <path d="M381.25 112a48 48 0 00-90.5 0H48v32h242.75a48 48 0 0090.5 0H464v-32zM176 208a48.09 48.09 0 00-45.25 32H48v32h82.75a48 48 0 0090.5 0H464v-32H221.25A48.09 48.09 0 00176 208zM336 336a48.09 48.09 0 00-45.25 32H48v32h242.75a48 48 0 0090.5 0H464v-32h-82.75A48.09 48.09 0 00336 336z"/>
                </svg>
              </button>
              <SliderDropDown
              style={{
                visibility: this.state.showFilters ? "visible" : "hidden"
              }}
              >
                <FlexRow>
                  <ConstWidthText>Quality</ConstWidthText>
                  <Range
                    value={ this.state.quality }
                    onChange={ (e) => this.setState({ quality: e }) }
                    min={0}
                    max={4}
                    step={.1}
                    marks={{
                      0: { label: 0 },
                      4: { label: 4 },
                    }}
                    trackStyle={[{
                      backgroundColor: "#85b8ba"
                    }]}
                    handleStyle={[
                      { borderColor: "#85b8ba" },
                      { borderColor: "#85b8ba" },
                    ]}
                  />
                </FlexRow>
                <FlexRow>
                  <ConstWidthText>Difficulty</ConstWidthText>
                  <Range
                    value={ this.state.difficulty }
                    onChange={ (e) => this.setState({ difficulty: e }) }
                    min={0}
                    max={4}
                    step={.1}
                    marks={{
                      0: { label: 0 },
                      4: { label: 4 },
                    }}
                    trackStyle={[{
                      backgroundColor: "#85b8ba"
                    }]}
                    handleStyle={[
                      { borderColor: "#85b8ba" },
                      { borderColor: "#85b8ba" },
                    ]}
                  />
                </FlexRow>
                <FlexRow>
                  <ConstWidthText>Work</ConstWidthText>
                  <Range
                    value={ this.state.work }
                    onChange={ (e) => this.setState({ work: e }) }
                    min={0}
                    max={4}
                    step={.1}
                    marks={{
                      0: { label: 0 },
                      4: { label: 4 },
                    }}
                    trackStyle={[{
                      backgroundColor: "#85b8ba"
                    }]}
                    handleStyle={[
                      { borderColor: "#85b8ba" },
                      { borderColor: "#85b8ba" },
                    ]}
                  />
                </FlexRow>
              </SliderDropDown>
            </div>
          </Search>
        </SearchWrapper>
        { this.state.departmentOptions.length > 0 &&
          <>
            { showCategoryHeaders && 
              <ResultCategoryComponent
              category="DEPARTMENTS"
              isFolded={this.state.departmentsFolded}
              setIsFolded={(e) => this.setState({ departmentsFolded: e })}
              />
              }
            { !this.state.departmentsFolded &&
              <PreviewWrapper>{departmentPreviews}</PreviewWrapper>
              }
          </>
          }  
        { this.state.courseOptions.length > 0 &&
          <>
            { showCategoryHeaders && 
              <ResultCategoryComponent
              category="COURSES"
              isFolded={this.state.coursesFolded}
              setIsFolded={(e) => this.setState({ coursesFolded: e })}
              />
              }
            { !this.state.coursesFolded &&
              <PreviewWrapper>{coursePreviews}</PreviewWrapper>
              }
          </>
          }
        { this.state.instructorOptions.length > 0 &&
          <>
            { showCategoryHeaders && 
              <ResultCategoryComponent
              category="INSTRUCTORS"
              isFolded={this.state.instructorsFolded}
              setIsFolded={(e) => this.setState({ instructorsFolded: e })}
              />
              }
            { !this.state.instructorsFolded &&
              <PreviewWrapper>{instructorPreviews}</PreviewWrapper>
              }
          </>
          }
      </Wrapper>
    );
  }
}

export default withRouter(DeepSearchBar);
