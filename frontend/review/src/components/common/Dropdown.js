import React, { useState, useEffect } from 'react';

export const Dropdown = ({ name, children }) => {
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        setIsOpen(false);
    }, [name])
    return(
        <div className="dropdown">
            <button 
                className="btn btn-dropdown"
                onClick={() => setIsOpen(!isOpen)}
            >
                {name}
            </button>
            {isOpen && <div className="dropdown-content">{children}</div>}
        </div>
    )
};
