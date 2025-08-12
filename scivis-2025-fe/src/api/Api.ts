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
  /** Index */
  index?: number;
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
  data = {
    /**
     * No description
     *
     * @name GetDataDescriptionDataDescriptionGet
     * @summary Get Data Description
     * @request GET:/data/description
     */
    getDataDescriptionDataDescriptionGet: (params: RequestParams = {}) =>
      this.request<DataDescription, any>({
        path: `/data/description`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetDataDataGet
     * @summary Get Data
     * @request GET:/data/
     */
    getDataDataGet: (params: RequestParams = {}) =>
      this.request<DataPoints, any>({
        path: `/data/`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetColumnTypesDataColumnTypesGet
     * @summary Get Column Types
     * @request GET:/data/column_types
     */
    getColumnTypesDataColumnTypesGet: (params: RequestParams = {}) =>
      this.request<Record<string, string[]>, any>({
        path: `/data/column_types`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetEmbeddingDataEmbeddingColTypeGet
     * @summary Get Embedding
     * @request GET:/data/embedding/{col_type}
     */
    getEmbeddingDataEmbeddingColTypeGet: (
      colType: string,
      params: RequestParams = {},
    ) =>
      this.request<number[][], HTTPValidationError>({
        path: `/data/embedding/${colType}`,
        method: "GET",
        format: "json",
        ...params,
      }),
  };
  dataPoint = {
    /**
     * No description
     *
     * @name GetSimilarDataPointDataPointSimilarityScoresIndexGet
     * @summary Get Similar Data Point
     * @request GET:/data-point/similarity-scores/{index}
     */
    getSimilarDataPointDataPointSimilarityScoresIndexGet: (
      index: number,
      params: RequestParams = {},
    ) =>
      this.request<number[], HTTPValidationError>({
        path: `/data-point/similarity-scores/${index}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetDataPointDataPointIdxIndexGet
     * @summary Get Data Point
     * @request GET:/data-point/idx/{index}
     */
    getDataPointDataPointIdxIndexGet: (
      index: number,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint, HTTPValidationError>({
        path: `/data-point/idx/${index}`,
        method: "GET",
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetInterpolationDataPointInterpolationGet
     * @summary Get Interpolation
     * @request GET:/data-point/interpolation
     */
    getInterpolationDataPointInterpolationGet: (
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
        path: `/data-point/interpolation`,
        method: "GET",
        query: query,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name GetSimilarDataPointsDataPointSimilarPost
     * @summary Get Similar Data Points
     * @request POST:/data-point/similar
     */
    getSimilarDataPointsDataPointSimilarPost: (
      data: DataPointSimilarity,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint[], HTTPValidationError>({
        path: `/data-point/similar`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name ExplanationsForDpDataPointExplanationsIdxPost
     * @summary Explanations For Dp
     * @request POST:/data-point/explanations/{idx}
     */
    explanationsForDpDataPointExplanationsIdxPost: (
      idx: number,
      data: DataPointSensitivity,
      params: RequestParams = {},
    ) =>
      this.request<SensitivityAnalysisResult[], HTTPValidationError>({
        path: `/data-point/explanations/${idx}`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),

    /**
     * No description
     *
     * @name DataPointSuggestionsDataPointSuggestionsPost
     * @summary Data Point Suggestions
     * @request POST:/data-point/suggestions
     */
    dataPointSuggestionsDataPointSuggestionsPost: (
      data: DataPointSuggestions,
      params: RequestParams = {},
    ) =>
      this.request<DataPoint[], HTTPValidationError>({
        path: `/data-point/suggestions`,
        method: "POST",
        body: data,
        type: ContentType.Json,
        format: "json",
        ...params,
      }),
  };
}
