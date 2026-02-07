/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/**
 * DataDescription
 * DataDescription model to describe the data structure.
 */
export interface DataDescription {
  /** Input Cols */
  input_cols: string[];
  /** Output Cols */
  output_cols: string[];
  /** All Columns */
  all_columns: string[];
  /** Num Samples */
  num_samples: number;
  /** Num Features */
  num_features: number;
  /** Num Outputs */
  num_outputs: number;
  /** Min Values */
  min_values: Record<string, number>;
  /** Max Values */
  max_values: Record<string, number>;
  /** Mean Values */
  mean_values: Record<string, number>;
  /** Std Values */
  std_values: Record<string, number>;
  /**
   * Inputs Constrained
   * @default true
   */
  inputs_constrained?: boolean;
}

/**
 * DataPoint
 * DataPoint model to represent a single data point.
 */
export interface DataPoint {
  /** Inputs */
  inputs: number[];
  /** Outputs */
  outputs: number[];
  /** Projected Outputs */
  projected_outputs?: number[];
  /** Uncertainties */
  uncertainties?: number[];
  /** Index */
  index?: number;
}

/** DataPointMinimzer */
export interface DataPointMinimzer {
  /**
   * Targets
   * @default []
   */
  targets?: LinearTarget[];
}

/** DataPointMinimzerInterpolation */
export interface DataPointMinimzerInterpolation {
  min: DataPointMinimzer;
  /** Start Idx */
  start_idx: number;
  /**
   * Samples
   * @default 256
   */
  samples?: number;
  /**
   * Div Penalty
   * @default 0.25
   */
  div_penalty?: number;
  /**
   * Cost Penalty
   * @default 0.25
   */
  cost_penalty?: number;
  /**
   * K Options
   * @default 3
   */
  k_options?: number;
}

/** DataPointSensitivity */
export interface DataPointSensitivity {
  /**
   * For Outputs
   * @default []
   */
  for_outputs?: string[];
  /**
   * Resolution
   * @default 16
   */
  resolution?: number;
}

/** DataPointSimilarity */
export interface DataPointSimilarity {
  /** Values */
  values: number[];
  /** K */
  k: number;
}

/** DataPointSuggestions */
export interface DataPointSuggestions {
  /** Base Index */
  base_index?: number;
  /**
   * Values
   * @default []
   */
  values?: number[];
  /**
   * K
   * @default 5
   */
  k?: number;
  /**
   * Weigh Changes
   * @default 1.5
   */
  weigh_changes?: number;
}

/**
 * DataPoints
 * DataPoint model to represent a single data point.
 */
export interface DataPoints {
  /** Inputs */
  inputs: number[][];
  /** Outputs */
  outputs: number[][];
  /** Projected Outputs */
  projected_outputs?: number[][];
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * InterpolationResult
 * InterpolationResult model to represent the result of interpolation.
 */
export interface InterpolationResult {
  /** Inputs */
  inputs: number[][];
  /** Outputs */
  outputs: number[][];
  /** Knn Inputs */
  knn_inputs: number[][];
  /** Knn Outputs */
  knn_outputs: number[][];
  /** Projected Outputs */
  projected_outputs: Record<string, number[][]>;
  /** Indices */
  indices: number[];
  /** Explainations */
  explainations?: number[][];
  /** Uncertainties */
  uncertainties?: number[][];
}

/** LinearTarget */
export interface LinearTarget {
  /** Name */
  name: string;
  /** Weight */
  weight: number;
  /** Val */
  val: number;
}

/** ManagerSettings */
export interface ManagerSettings {
  /** DataDescription model to describe the data structure. */
  data_description: DataDescription;
  /**
   * Mode
   * @default "tsne"
   */
  mode?: string;
  /**
   * Data Name
   * @default "Aloy Data"
   */
  data_name?: string;
  /**
   * Short Data Name
   * @default "scivis"
   */
  short_data_name?: string;
  /**
   * Input Cols
   * @default 6
   */
  input_cols?: number;
  /**
   * Output Cols
   * @default 64
   */
  output_cols?: number;
  /** Time Col */
  time_col?: number | null;
  /**
   * Inputs Constrained
   * @default true
   */
  inputs_constrained?: boolean;
  /**
   * Col Defs
   * @default {}
   */
  col_defs?: Record<string, string[]>;
  /**
   * Loaded
   * @default false
   */
  loaded?: boolean;
}

/**
 * SensitivityAnalysisResult
 * SensitivityAnalysisResult model to represent the result of sensitivity analysis.
 */
export interface SensitivityAnalysisResult {
  /** DataPoint model to represent a single data point. */
  dp: DataPoint;
  /** Sensitivity Scores */
  sensitivity_scores: number[];
  /** Out Col */
  out_col: string;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
}

import type {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  HeadersDefaults,
  ResponseType,
} from "axios";
import axios from "axios";

export type QueryParamsType = Record<string | number, any>;

export interface FullRequestParams
  extends Omit<AxiosRequestConfig, "data" | "params" | "url" | "responseType"> {
  /** set parameter to `true` for call `securityWorker` for this request */
  secure?: boolean;
  /** request path */
  path: string;
  /** content type of request body */
  type?: ContentType;
  /** query params */
  query?: QueryParamsType;
  /** format of response (i.e. response.json() -> format: "json") */
  format?: ResponseType;
  /** request body */
  body?: unknown;
}

export type RequestParams = Omit<
  FullRequestParams,
  "body" | "method" | "query" | "path"
>;

export interface ApiConfig<SecurityDataType = unknown>
  extends Omit<AxiosRequestConfig, "data" | "cancelToken"> {
  securityWorker?: (
    securityData: SecurityDataType | null,
  ) => Promise<AxiosRequestConfig | void> | AxiosRequestConfig | void;
  secure?: boolean;
  format?: ResponseType;
}

export enum ContentType {
  Json = "application/json",
  JsonApi = "application/vnd.api+json",
  FormData = "multipart/form-data",
  UrlEncoded = "application/x-www-form-urlencoded",
  Text = "text/plain",
}

export class HttpClient<SecurityDataType = unknown> {
  public instance: AxiosInstance;
  private securityData: SecurityDataType | null = null;
  private securityWorker?: ApiConfig<SecurityDataType>["securityWorker"];
  private secure?: boolean;
  private format?: ResponseType;

  constructor({
    securityWorker,
    secure,
    format,
    ...axiosConfig
  }: ApiConfig<SecurityDataType> = {}) {
    this.instance = axios.create({
      ...axiosConfig,
      baseURL: axiosConfig.baseURL || "",
    });
    this.secure = secure;
    this.format = format;
    this.securityWorker = securityWorker;
  }

  public setSecurityData = (data: SecurityDataType | null) => {
    this.securityData = data;
  };

  protected mergeRequestParams(
    params1: AxiosRequestConfig,
    params2?: AxiosRequestConfig,
  ): AxiosRequestConfig {
    const method = params1.method || (params2 && params2.method);

    return {
      ...this.instance.defaults,
      ...params1,
      ...(params2 || {}),
      headers: {
        ...((method &&
          this.instance.defaults.headers[
            method.toLowerCase() as keyof HeadersDefaults
          ]) ||
          {}),
        ...(params1.headers || {}),
        ...((params2 && params2.headers) || {}),
      },
    };
  }

  protected stringifyFormItem(formItem: unknown) {
    if (typeof formItem === "object" && formItem !== null) {
      return JSON.stringify(formItem);
    } else {
      return `${formItem}`;
    }
  }

  protected createFormData(input: Record<string, unknown>): FormData {
    if (input instanceof FormData) {
      return input;
    }
    return Object.keys(input || {}).reduce((formData, key) => {
      const property = input[key];
      const propertyContent: any[] =
        property instanceof Array ? property : [property];

      for (const formItem of propertyContent) {
        const isFileType = formItem instanceof Blob || formItem instanceof File;
        formData.append(
          key,
          isFileType ? formItem : this.stringifyFormItem(formItem),
        );
      }

      return formData;
    }, new FormData());
  }

  public request = async <T = any, _E = any>({
    secure,
    path,
    type,
    query,
    format,
    body,
    ...params
  }: FullRequestParams): Promise<AxiosResponse<T>> => {
    const secureParams =
      ((typeof secure === "boolean" ? secure : this.secure) &&
        this.securityWorker &&
        (await this.securityWorker(this.securityData))) ||
      {};
    const requestParams = this.mergeRequestParams(params, secureParams);
    const responseFormat = format || this.format || undefined;

    if (
      type === ContentType.FormData &&
      body &&
      body !== null &&
      typeof body === "object"
    ) {
      body = this.createFormData(body as Record<string, unknown>);
    }

    if (
      type === ContentType.Text &&
      body &&
      body !== null &&
      typeof body !== "string"
    ) {
      body = JSON.stringify(body);
    }

    return this.instance.request({
      ...requestParams,
      headers: {
        ...(requestParams.headers || {}),
        ...(type ? { "Content-Type": type } : {}),
      },
      params: query,
      responseType: responseFormat,
      data: body,
      url: path,
    });
  };
}

/**
 * @title FastAPI
 * @version 0.1.0
 */
export class Api<
  SecurityDataType extends unknown,
> extends HttpClient<SecurityDataType> {
  datasets = {
    /**
     * No description
     *
     * @name GetDatasetsDatasetsGet
     * @summary Get Datasets
     * @request GET:/datasets/
     */
    getDatasetsDatasetsGet: (params: RequestParams = {}) =>
      this.request<Record<string, ManagerSettings>, any>({
        path: `/datasets/`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name LoadDatasetDatasetsLoadSetNamePost
     * @summary Load Dataset
     * @request POST:/datasets/load/{set_name}
     */
    loadDatasetDatasetsLoadSetNamePost: (
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<ManagerSettings, HTTPValidationError>({
        path: `/datasets/load/${setName}`,
        method: "POST",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetSetDatasetsSetNameGet
     * @summary Get Set
     * @request GET:/datasets/{set_name}
     */
    getSetDatasetsSetNameGet: (
      setName: string,
      query?: {
        /**
         * Load
         * @default false
         */
        load?: boolean;
      },
      params: RequestParams = {},
    ) =>
      this.request<ManagerSettings, HTTPValidationError>({
        path: `/datasets/${setName}`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetDataDescriptionDatasetsSetNameDataDescriptionGet
     * @summary Get Data Description
     * @request GET:/datasets/{set_name}/data/description
     */
    getDataDescriptionDatasetsSetNameDataDescriptionGet: (
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<DataDescription, HTTPValidationError>({
        path: `/datasets/${setName}/data/description`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetDataDatasetsSetNameDataGet
     * @summary Get Data
     * @request GET:/datasets/{set_name}/data/
     */
    getDataDatasetsSetNameDataGet: (
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<DataPoints, HTTPValidationError>({
        path: `/datasets/${setName}/data/`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetColumnTypesDatasetsSetNameDataColumnTypesGet
     * @summary Get Column Types
     * @request GET:/datasets/{set_name}/data/column_types
     */
    getColumnTypesDatasetsSetNameDataColumnTypesGet: (
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<Record<string, string[]>, HTTPValidationError>({
        path: `/datasets/${setName}/data/column_types`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetEmbeddingDatasetsSetNameDataEmbeddingColTypeGet
     * @summary Get Embedding
     * @request GET:/datasets/{set_name}/data/embedding/{col_type}
     */
    getEmbeddingDatasetsSetNameDataEmbeddingColTypeGet: (
      colType: string,
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<number[][], HTTPValidationError>({
        path: `/datasets/${setName}/data/embedding/${colType}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetObjectiveCostsDatasetsSetNameDataPointMinimizeCostPost
     * @summary Get Objective Costs
     * @request POST:/datasets/{set_name}/data-point/minimize/cost
     */
    getObjectiveCostsDatasetsSetNameDataPointMinimizeCostPost: (
      setName: string,
      data: DataPointMinimzer,
      params: RequestParams = {},
    ) =>
      this.request<number[], HTTPValidationError>({
        path: `/datasets/${setName}/data-point/minimize/cost`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetMinimizationInterpolationDatasetsSetNameDataPointMinimizeInterpolationPost
     * @summary Get Minimization Interpolation
     * @request POST:/datasets/{set_name}/data-point/minimize/interpolation
     */
    getMinimizationInterpolationDatasetsSetNameDataPointMinimizeInterpolationPost:
      (
        setName: string,
        data: DataPointMinimzerInterpolation,
        params: RequestParams = {},
      ) =>
        this.request<InterpolationResult[], HTTPValidationError>({
          path: `/datasets/${setName}/data-point/minimize/interpolation`,
          method: "POST",
          body: data,
          type: ContentType.Json,
          format: "json",
          ...params,
        }),

    /**
     * No description
     *
     * @name GetSimilarDataPointDatasetsSetNameDataPointSimilarityScoresIndexGet
     * @summary Get Similar Data Point
     * @request GET:/datasets/{set_name}/data-point/similarity-scores/{index}
     */
    getSimilarDataPointDatasetsSetNameDataPointSimilarityScoresIndexGet: (
      index: number,
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<number[], HTTPValidationError>({
        path: `/datasets/${setName}/data-point/similarity-scores/${index}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetDataPointDatasetsSetNameDataPointIdxIndexGet
     * @summary Get Data Point
     * @request GET:/datasets/{set_name}/data-point/idx/{index}
     */
    getDataPointDatasetsSetNameDataPointIdxIndexGet: (
      index: number,
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint, HTTPValidationError>({
        path: `/datasets/${setName}/data-point/idx/${index}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetInterpolationDatasetsSetNameDataPointInterpolationGet
     * @summary Get Interpolation
     * @request GET:/datasets/{set_name}/data-point/interpolation
     */
    getInterpolationDatasetsSetNameDataPointInterpolationGet: (
      setName: string,
      query: {
        /** From Index */
        from_index: number;
        /** To Index */
        to_index: number;
        /**
         * N Samples
         * @default 128
         */
        n_samples?: any;
        /**
         * Embedding Type
         * @default "all"
         */
        embedding_type?: string;
        /**
         * Include Explainations
         * @default false
         */
        include_explainations?: boolean;
      },
      params: RequestParams = {},
    ) =>
      this.request<InterpolationResult, HTTPValidationError>({
        path: `/datasets/${setName}/data-point/interpolation`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetSimilarDataPointsDatasetsSetNameDataPointSimilarPost
     * @summary Get Similar Data Points
     * @request POST:/datasets/{set_name}/data-point/similar
     */
    getSimilarDataPointsDatasetsSetNameDataPointSimilarPost: (
      setName: string,
      data: DataPointSimilarity,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint[], HTTPValidationError>({
        path: `/datasets/${setName}/data-point/similar`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name ExplanationsForDpDatasetsSetNameDataPointExplanationsIdxPost
     * @summary Explanations For Dp
     * @request POST:/datasets/{set_name}/data-point/explanations/{idx}
     */
    explanationsForDpDatasetsSetNameDataPointExplanationsIdxPost: (
      idx: number,
      setName: string,
      data: DataPointSensitivity,
      params: RequestParams = {},
    ) =>
      this.request<SensitivityAnalysisResult[], HTTPValidationError>({
        path: `/datasets/${setName}/data-point/explanations/${idx}`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name DataPointSuggestionsDatasetsSetNameDataPointSuggestionsPost
     * @summary Data Point Suggestions
     * @request POST:/datasets/{set_name}/data-point/suggestions
     */
    dataPointSuggestionsDatasetsSetNameDataPointSuggestionsPost: (
      setName: string,
      data: DataPointSuggestions,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint[], HTTPValidationError>({
        path: `/datasets/${setName}/data-point/suggestions`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name PosteriorOfDataPointDatasetsSetNameDataPointPosteriorIndexGet
     * @summary Posterior Of Data Point
     * @request GET:/datasets/{set_name}/data-point/posterior/{index}
     */
    posteriorOfDataPointDatasetsSetNameDataPointPosteriorIndexGet: (
      index: number,
      setName: string,
      params: RequestParams = {},
    ) =>
      this.request<any, HTTPValidationError>({
        path: `/datasets/${setName}/data-point/posterior/${index}`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
}
