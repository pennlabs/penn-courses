import React, { useMemo } from 'react';
import styled from 'styled-components';
import { PiPlus, PiPlusThin } from "react-icons/pi";
import { HiMagnifyingGlass, HiXMark } from "react-icons/hi2";
import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { use } from 'react';
import { apiAutocomplete } from '../utils/api';

const SelectBoxContainer = styled.div`
    display: flex;
    padding: 12px;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 10px;
    align-self: stretch;
    margin-bottom: 12px;
    border-radius: 10px;
    background: #EFF1F5;
    color: #545454;
    font-family: 'SFPro', sans-serif;
    font-size: 14px;
    font-style: normal;
    font-weight: 400;
    cursor: pointer;
    max-width: 400px;
`;

const SelectSearchBarContainer = styled.div`
    display: flex;
    flex-direction: column;
    width: 100%;
    padding: 9px 8px;
    align-items: flex-start;
    gap: 15px;
    position: absolute;
    left: 0;
    top: 0;
    border-radius: 10px;
    background: #FFFFFF;
    z-index: 50; 
    max-height: 180px;
    cursor: pointer;

    ${props => props.$isSearchFocused && `
        border: 1px solid #EBEEF2;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    `}
`;

const SelectSearchBar = styled.input`
    width: 100%;
    border: none;
    outline: none;
    background: transparent;
    font-size: 14px;
    font-family: 'SFPro', sans-serif;
    font-weight: 400;
    color: #545454;
`;

const SelectSearchResultsContainer = styled.div`
    display: flex;
    gap: 10px;
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
    overflow-y: auto;
`;

const OptionContainer = styled.div`
    display: flex;
    width: 73px;
    height: 29px;
    padding: 6px 11px;
    align-items: center;
    gap: 1px;
    border-radius: 10px;
    cursor: pointer;

    ${props => props.$fullWidth && `
        width: fit-content;
        max-width: none;
    `}
`;

const placeholderOptions = ['AMHR', 'ANAT', 'AAFD', 'ACFS', 'ANTH', 'ARTH'];
// Placeholder options for select box, get from backend later

export const useOnClickOutside = (refList, handler) => {
    useEffect(() => {
        const listener = (event) => {
            for(const ref of refList) {
                if (!ref.current) continue;
                if (event.composedPath().includes(ref.current)) {
                    return;
                }
            }
            handler(event)
        };

        document.addEventListener('mousedown', listener);
        document.addEventListener('touchstart', listener);

        return () => {
            document.removeEventListener('mousedown', listener);
            document.removeEventListener('touchstart', listener);
        };
    }, [refList, handler]); 
};

const OptionBox = ({ text, isActive, filterOptionsList, setFilterOptionsList, visualOptionsList, setVisualOptionsList, fullWidth }) => {
    const [isSelected, setIsSelected] = useState(isActive);

    useEffect(() => {
        if (filterOptionsList.includes(text) && !isSelected) {
            setFilterOptionsList(filterOptionsList.filter(option => option !== text));
        } else if (!filterOptionsList.includes(text) && isSelected) {
            setFilterOptionsList([...filterOptionsList, text]);
        }
    }, [isSelected]);

    return (
        <>
            <OptionContainer $fullWidth={fullWidth}onClick={() => setIsSelected(!isSelected)}
                style={{ 
                    background: isSelected ? '#3E3E40' :'#FFFFFF', 
                    border: isSelected ? 'none' : '2px solid #D9D9D9', 
                    color: isSelected ? '#FFF' : '#545454' 
                }}>
                <div style={{ fontSize: '12px', overflow: fullWidth ? 'none' : 'hidden', whiteSpace: 'nowrap', minWidth: '38px' }}>
                    {text}
                </div>
                {isSelected ? (
                    <HiXMark size={15} color="#FFFFFF" />
                ) : (
                    <>
                        {visualOptionsList.has(text) ? (
                            <HiXMark size={15} color="#3E3E40" onClick={() => {
                                setVisualOptionsList(prev => {
                                    const newSet = new Set(prev);
                                    newSet.delete(text);
                                    return newSet;
                                });
                            }}/>
                        ) : (
                            <PiPlus size={15} color="#3E3E40" />
                        )}
                    </>
                )}
            </OptionContainer>
        </>
    );
}

const SelectBox = ({ options, setOptions, availableItems, fullWidth = false }) => {

    const [visualStoredOptions, setVisualStoredOptions] = useState(new Set(options));
    //this is to show the already selected options, but not the ones selected in the search bar

    const [searchResultOptions, setSearchResultOptions] = useState([]); 
    // This is the list of options shown in the search dropdown, which changes as you search
    
    const [isSearchFocused, setIsSearchFocused] = useState(false);

    const [searchQuery, setSearchQuery] = useState('');

    const wrapperRef = useRef(null);
    const floatingRef = useRef(null);

    const isInternalUpdate = useRef(false);

    const handleSetOptions = (newOptions) => {
        isInternalUpdate.current = true;
        setOptions(newOptions);
    };

    useEffect(() => {
        if (isInternalUpdate.current) {
            // We caused this update internally. Reset the flag and do nothing.
            isInternalUpdate.current = false;
        } else {
            setVisualStoredOptions(new Set([...visualStoredOptions, ...options]));
        }
    }, [options]);

    useOnClickOutside([wrapperRef, floatingRef], () => {
        if (isSearchFocused) {
            closeSearchBar();
        }
    });

    useEffect(() => {
        console.log('Available items:', availableItems);
        const filteredOptions = availableItems.filter(option => {
            const isNotSelected = !visualStoredOptions.has(option);
            const matchesSearch = option.toLowerCase().includes(searchQuery.toLowerCase());
            return isNotSelected && matchesSearch;
        });
        setSearchResultOptions(filteredOptions);
    }, [visualStoredOptions, searchQuery]); 

    // Extracted content so we can clone it
    const searchBarContent = (
        <>
            <div 
                onMouseDown={() => {
                    setIsSearchFocused(true);
                }}
                style={{ display: 'flex', gap: '10px', width: '100%' }}>
                <HiMagnifyingGlass size={20} color="#A1A1A1" />
                <SelectSearchBar 
                    type="text" 
                    placeholder="Search"
                    value={searchQuery}
                    onChange={(e) => {
                        const newQuery = e.target.value;
                        const searchBarOnlyOptions = options.filter(option => !visualStoredOptions.has(option));
                        const newVisualOptions = searchBarOnlyOptions.filter(option => option.toLowerCase().includes(newQuery.toLowerCase()));
                        setVisualStoredOptions(new Set([...visualStoredOptions, ...newVisualOptions]));
                        setSearchQuery(newQuery);
                    }}
                />
            </div>
            {isSearchFocused && (
                <SelectSearchResultsContainer className='no-scrollbar'>
                    {searchResultOptions.length === 0 ? (
                        <p style={{ color: '#A1A1A1', fontStyle: 'italic' }}>No options available</p>
                    ) : (
                        <>
                            {searchResultOptions.slice(0, 51).map((option) => (
                                <OptionBox
                                    key={`search-${option}`} 
                                    text={option}
                                    isActive={options.includes(option)}
                                    filterOptionsList={options}
                                    setFilterOptionsList={handleSetOptions}
                                    visualOptionsList={visualStoredOptions}
                                    setVisualOptionsList={setVisualStoredOptions}
                                    fullWidth={fullWidth}
                                />
                            ))}
                        {searchResultOptions.length > 51 && <p style={{ color: '#A1A1A1', fontStyle: 'italic', width: '100%' }}>Showing first 50 results</p>}
                        </>
                    )}
                </SelectSearchResultsContainer>
            )}
        </>
    );

    const closeSearchBar = () => {
        setIsSearchFocused(false);
        setVisualStoredOptions(prev => new Set([...prev, ...options]));
        setSearchQuery('');
    };

    return (
        <div ref={wrapperRef} style={{width: '100%'}}>
            <SelectBoxContainer 
                onMouseDown={(event) => {
                    if (!floatingRef.current?.contains(event.target)) {
                        if(isSearchFocused) {
                            closeSearchBar();
                        } else if (visualStoredOptions.size === 0) {
                            setIsSearchFocused(true);
                            setTimeout(() => {
                                const targetElement = floatingRef.current;
                                if (targetElement) {
                                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
                                }
                            }, 350); // matches framer motion exit/enter durations
                        }
                    }
                }}
            >   
                {visualStoredOptions.size === 0 ? (
                    <div 
                        style={{ display: 'flex', gap: '10px', width: '100%', alignItems: 'center' }}
                    >
                        {isSearchFocused ? (
                            <p>None selected</p>
                        ): (
                            <>
                                <p>None selected</p>
                                <PiPlusThin size={20} color="#A1A1A1" />
                            </>
                        )}
                    </div>
                ) : (
                    <div style={{ display: 'flex', gap: '10px', width: '100%', flexWrap: 'wrap' }}>
                        {[...visualStoredOptions].map((option) => (
                            <OptionBox 
                                key={`selected-${option}`} 
                                text={option} 
                                isActive={options.includes(option)} 
                                filterOptionsList={options} 
                                setFilterOptionsList={handleSetOptions}
                                visualOptionsList={visualStoredOptions}
                                setVisualOptionsList={setVisualStoredOptions}
                                fullWidth={fullWidth}
                            />
                        ))}
                    </div>
                )}

                <AnimatePresence initial={false}>
                    {(isSearchFocused || visualStoredOptions.size > 0) && (
                        <motion.div
                            initial={{ opacity: 0, y: -5, height: 0 }}
                            animate={{ opacity: 1, y: 0, height: '40px' }}
                            exit={{ opacity: 0, y: -5, height: 0 }}
                            transition={{ duration: 0.2 }}
                            style={{ position: 'relative', width: '100%' }}
                        >
                            <SelectSearchBarContainer ref={floatingRef} $isSearchFocused={isSearchFocused}>
                                {searchBarContent}
                            </SelectSearchBarContainer>
                        </motion.div>
                    )}
                </AnimatePresence>

            </SelectBoxContainer>

            {/* invisible clones sits outside the gray box */}
            <AnimatePresence initial={false}>
                {(isSearchFocused || visualStoredOptions.size > 0) && (
                    <motion.div 
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
                        style={{ 
                            overflow: 'hidden', 
                            visibility: 'hidden', 
                            pointerEvents: 'none' 
                        }}
                    >
                        <div style={{ 
                            display: 'flex', 
                            flexDirection: 'column', 
                            gap: '10px', 
                            padding: '9px 8px', 
                            width: 'calc(100% - 20px)',
                            maxHeight: '180px', 
                            marginTop: '-52px' 
                        }}>
                            {searchBarContent}
                        </div>
                    </motion.div> 
                )}
            </AnimatePresence>
        </div>
    );
}

export default SelectBox;
