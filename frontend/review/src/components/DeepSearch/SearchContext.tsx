import React, { useState } from "react"

export interface SearchContextType {
	query?: string
}

const SearchContext = React.createContext<SearchContextType>({})

export const SearchContextProvider: React.FC<{
	query?: string;
	children: React.ReactNode;
}> = ({ query, children }) => {
	return (
		<SearchContext.Provider value={{ query }}>
			{children}
		</SearchContext.Provider>
	)
}

export const useSearchContext = () => React.useContext(SearchContext)

export default SearchContextProvider
