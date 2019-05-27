/* eslint-disable react/prop-types */
// This file should be refactored
import React, { Component } from "react";

export class OutClickable extends Component {
    // a component that you can "click out" of
    // requires that ref={this.setWrapperRef} is added as an attribute
    constructor(props) {
        super(props);
        document.addEventListener("click", this.handleClickOutside);
    }

    /**
     * Alert if clicked on outside of element
     */
    handleClickOutside = (event) => {
        const {
            allowed,
        } = this.props;
        if (this.wrapperRef && !this.wrapperRef.contains(event.target)) {
            if (allowed) {
                const allowedElements = allowed.map(id => document.getElementById(id));
                if (allowedElements.reduce((acc, item) => acc
                    || item.contains(event.target), false)) {
                    return;
                }
            }
            this.collapse();
        }
    }

    setWrapperRef = (node) => {
        this.wrapperRef = node;
    }
}

export class Dropdown extends OutClickable {
    constructor(props) {
        super(props);
        const {
            defActive,
            defText,
        } = this.props;
        let startingActivity = -1;
        // if props.defActive is not defined, it is assumed that the dropdown does not control
        // state and instead initiates an action
        if (defActive) {
            startingActivity = defActive;
        }
        this.state = { active: false, activity: startingActivity, label_text: defText };
    }

    // Instead of doing this, can just read props directly
    componentWillReceiveProps(props) {
        let startingActivity = -1;
        // if props.defActive is not defined, it is assumed that the dropdown does not control
        // state and instead initiates an action
        if (props.defActive) {
            startingActivity = props.defActive;
        }
        this.setState({ activity: startingActivity, label_text: props.defText });
    }

    collapse = () => {
        this.setState(state => ({ active: false }));
    }

    toggleDropdown = () => {
        if (this.state.active) {
            this.collapse();
        } else {
            this.activateDropdown();
        }
    }

    activateDropdown = () => {
        this.setState(state => ({ active: true }));
    }

    activateItem = (i) => {
        const {
            updateLabel,
            contents,
            defActive,
        } = this.props;
        this.setState(state => ({ activity: i }));
        if (updateLabel) {
            // updates the label for the dropdown if this property is applied in JSX
            this.setState(state => ({ label_text: contents[i][0] }));
        }
        this.collapse();
        // if no default activity was selected, assumes that the item in the
        // dropdown should not remain highlighted
        // This is because if props.defActive is not defined,
        // it is assumed that the dropdown does not control
        // state and instead initiates an action
        if (defActive === undefined) {
            this.setState(state => ({ activity: -1 }));
        }
    }

    render() {
        const {
            contents,
            id,
        } = this.props;
        const aList = [];
        for (let i = 0; i < contents.length; i += 1) {
            let addition = "";
            if (this.state.activity === i) {
                addition = " is-active";
            }
            const selectedContents = contents[i];
            aList.push(
                <button
                    onClick={() => {
                        if (selectedContents.length > 1) {
                            // this means that a function for onclick is provided
                            selectedContents[1]();
                        }
                        this.activateItem(i);
                    }}
                    type="button"
                    className={`dropdown-item${addition} button`}
                    style={{ border: "none", marginBottom: "0.2em" }}
                    key={i}
                >
                    {selectedContents[0]}
                </button>
            );
        }
        let addition = "";
        if (this.state.active) {
            addition = " is-active";
        }
        return (
            <div id={id} ref={this.setWrapperRef} className={`dropdown${addition}`}>
                <div className="dropdown-trigger" onClick={this.toggleDropdown} role="button">
                    <button
                        className="button"
                        aria-haspopup={true}
                        aria-controls="dropdown-menu"
                        type="button"
                    >
                        <span>
                            <span className="selected_name">{this.state.label_text}</span>
                            <span className="icon is-small">
                                <i className="fa fa-angle-down" aria-hidden="true" />
                            </span>
                        </span>
                    </button>
                </div>
                <div className="dropdown-menu" role="menu">
                    <div className="dropdown-content">
                        {aList}
                    </div>
                </div>
            </div>
        );
    }
}


// export class ToggleButton extends OutClickable {
//     // not a dropdown itself, but interacts with adjacent elements via css
//     constructor(props) {
//         super(props);
//         this.props = props;
//         this.containerHTML = props.parent.innerHTML;
//         this.state = { active: false };
//         this.closeDropdown = this.closeDropdown.bind(this);
//         this.activateDropdown = this.activateDropdown.bind(this);
//     }

//     activateDropdown() {
//         this.setState(state => ({ active: true }));
//     }

//     closeDropdown() {
//         this.setState(state => ({ active: false }));
//     }

//     render() {
//         return (
//             <button
//                 ref={this.setWrapperRef}
//                 className={`toggle_button ${this.state.active}`}
//                 type="button"
//             >
//                 {this.props.name}
//             </button>
//         );
//     }
// }
