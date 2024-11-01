declare module 'workerize-loader!*' {
    const worker: any;
    export = worker;
}

declare module 'workerize-loader!../workers/autocomplete.worker' {
    interface AutocompleteWorker {
        compress(data: string): string;
        decompress(data: string): string;
    }
    const worker: () => AutocompleteWorker;
    export = worker;
}