import useSWR from "swr";

const usePlatformOptions = () => {
    const { data: options, error } = useSWR(
        "https://platform.pennlabs.org/options/",
        ([url, init]) => fetch(url, init).then(res => res.json())
    );

    return { options, error };
};

export default usePlatformOptions;
